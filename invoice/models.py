from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django_extensions.db.fields import AutoSlugField

from store.models import Item

ZERO = Decimal('0.00')
CENT = Decimal('0.01')


class Invoice(models.Model):
    """
    An invoice for a quantity of one item, plus shipping.
    Totals are always computed from price, quantity and shipping.
    """

    slug = AutoSlugField(unique=True, populate_from='customer_name')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Invoice date')
    customer_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=20)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    price_per_item = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name='Price Per Item (Ksh)',
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('1.00'),
        validators=[MinValueValidator(CENT)],
    )
    shipping = models.DecimalField(
        max_digits=12, decimal_places=2, default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name='Shipping and Handling',
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, editable=False,
        verbose_name='Total Amount (Ksh)',
    )
    grand_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, editable=False,
        verbose_name='Grand Total (Ksh)',
    )

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        self.quantity = Decimal(str(self.quantity))
        self.price_per_item = Decimal(str(self.price_per_item))
        self.shipping = Decimal(str(self.shipping or 0))
        self.total = (self.quantity * self.price_per_item).quantize(CENT, ROUND_HALF_UP)
        self.grand_total = (self.total + self.shipping).quantize(CENT, ROUND_HALF_UP)
        return super().save(*args, **kwargs)

    @property
    def invoice_number(self):
        return f'INV{self.pk:06d}' if self.pk else ''

    def get_absolute_url(self):
        return reverse('invoice-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.invoice_number or self.slug
