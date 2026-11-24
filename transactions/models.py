from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.urls import reverse
from django_extensions.db.fields import AutoSlugField

from store.models import Item
from accounts.models import Vendor, Customer

DELIVERY_CHOICES = [("P", "Pending"), ("S", "Successful")]

ZERO = Decimal('0.00')


def money_field(**kwargs):
    kwargs.setdefault('max_digits', 12)
    kwargs.setdefault('decimal_places', 2)
    kwargs.setdefault('default', ZERO)
    return models.DecimalField(**kwargs)


class Sale(models.Model):
    """
    A completed point of sale transaction.

    All amounts are computed on the server (see transactions.services); the
    browser only sends item ids, quantities, tax rate, amount paid and any
    loyalty points to redeem. Sales are voided, never hard deleted, so the
    audit trail and receipt numbers stay intact.
    """

    STATUS_COMPLETED = 'C'
    STATUS_VOIDED = 'V'
    STATUS_CHOICES = [(STATUS_COMPLETED, 'Completed'), (STATUS_VOIDED, 'Voided')]

    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Sale Date")
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, db_column="customer"
    )
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales_served',
    )
    sub_total = money_field()
    discount_amount = money_field(verbose_name='Loyalty discount')
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=ZERO,
        validators=[MinValueValidator(ZERO), MaxValueValidator(Decimal('100'))],
    )
    tax_amount = money_field()
    grand_total = money_field()
    amount_paid = money_field()
    amount_change = money_field()

    loyalty_points_redeemed = models.PositiveIntegerField(default=0)
    loyalty_points_earned = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=STATUS_COMPLETED, db_index=True
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales_voided',
    )
    void_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "sales"
        ordering = ['-date_added']
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        return f"Sale {self.receipt_number} | {self.grand_total}"

    def get_absolute_url(self):
        return reverse('sale-detail', kwargs={'pk': self.pk})

    @property
    def receipt_number(self):
        return f"IMS{self.pk:06d}" if self.pk else ''

    @property
    def is_voided(self):
        return self.status == self.STATUS_VOIDED

    def sum_products(self):
        """Total number of units sold in this sale."""
        return sum(detail.quantity for detail in self.saledetail_set.all())


class SaleDetail(models.Model):
    """
    One line of a sale. Price is the unit price at the time of sale.
    """

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        db_column="sale",
        related_name="saledetail_set"
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT, db_column="item")
    price = money_field(default=None)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_detail = money_field(default=None)

    class Meta:
        db_table = "sale_details"
        verbose_name = "Sale Detail"
        verbose_name_plural = "Sale Details"

    def __str__(self):
        return f"{self.item} x {self.quantity} (sale {self.sale_id})"


class LoyaltyTransaction(models.Model):
    """
    Ledger of every change to a customer's loyalty balance.
    The balance on Customer always equals the sum of this ledger.
    """

    EARN = 'EARN'
    REDEEM = 'REDEEM'
    REVERSAL = 'REVERSAL'
    ADJUST = 'ADJUST'
    KIND_CHOICES = [
        (EARN, 'Earned on sale'),
        (REDEEM, 'Redeemed on sale'),
        (REVERSAL, 'Reversed (sale voided)'),
        (ADJUST, 'Manual adjustment'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='loyalty_transactions'
    )
    sale = models.ForeignKey(
        Sale, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='loyalty_transactions',
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    points = models.IntegerField(help_text='Positive adds points, negative removes them.')
    balance_after = models.PositiveIntegerField()
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.customer} {self.points:+d} ({self.get_kind_display()})"


class Purchase(models.Model):
    """
    A purchase order for an item from a vendor.

    Stock is received only when the delivery status is Successful.
    ``stock_applied`` records how many units this purchase has added to stock,
    so edits, status changes and deletes adjust stock by the difference
    instead of adding the full quantity again.
    """

    slug = AutoSlugField(unique=True, populate_from="vendor")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    description = models.TextField(max_length=300, blank=True, null=True)
    vendor = models.ForeignKey(
        Vendor, related_name="purchases", on_delete=models.PROTECT
    )
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Delivery Date"
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    delivery_status = models.CharField(
        choices=DELIVERY_CHOICES,
        max_length=1,
        default="P",
        verbose_name="Delivery Status",
    )
    price = money_field(
        verbose_name="Price per item (Ksh)",
        validators=[MinValueValidator(ZERO)],
    )
    total_value = money_field(editable=False)
    stock_applied = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.item.name} from {self.vendor.name}"

    @property
    def received(self):
        return self.delivery_status == 'S'

    def _target_stock(self):
        return self.quantity if self.received else 0

    def save(self, *args, **kwargs):
        self.quantity = int(self.quantity)
        self.price = Decimal(str(self.price or 0))
        self.total_value = self.price * self.quantity
        with transaction.atomic():
            previous = None
            if self.pk:
                previous = (
                    Purchase.objects.select_for_update()
                    .filter(pk=self.pk).values('item_id', 'stock_applied').first()
                )
            target = self._target_stock()
            if previous and previous['item_id'] != self.item_id:
                # Item changed: take stock back from the old item, give to new.
                Item.adjust_stock(previous['item_id'], -previous['stock_applied'])
                Item.adjust_stock(self.item_id, target)
            else:
                applied = previous['stock_applied'] if previous else 0
                Item.adjust_stock(self.item_id, target - applied)
            self.stock_applied = target
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            applied = (
                Purchase.objects.select_for_update()
                .filter(pk=self.pk).values_list('stock_applied', flat=True).first()
            ) or 0
            Item.adjust_stock(self.item_id, -applied)
            return super().delete(*args, **kwargs)
