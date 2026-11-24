"""
Models for categories, items (stock) and deliveries.

Stock levels are only changed through ``Item.adjust_stock`` which locks the
row and refuses to go below zero, so concurrent tills cannot oversell.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField

from accounts.models import Vendor


class InsufficientStock(ValidationError):
    pass


class Category(models.Model):
    """
    Represents a category for items.
    """
    name = models.CharField(max_length=50)
    slug = AutoSlugField(unique=True, populate_from='name')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'


class Item(models.Model):
    """
    Represents an item in the inventory.
    """
    slug = AutoSlugField(unique=True, populate_from='name')
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=256, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    expiring_date = models.DateTimeField(null=True, blank=True)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        return self.quantity > 0

    def to_json(self):
        """Shape used by the point of sale item search."""
        return {
            'id': self.id,
            'text': self.name,
            'name': self.name,
            'category': self.category.name if self.category_id else '',
            'price': str(self.price),
            'stock': self.quantity,
            'quantity': 1,
            'total_item': str(self.price),
        }

    @classmethod
    def adjust_stock(cls, item_id, delta):
        """
        Atomically add ``delta`` (may be negative) to an item's stock.
        Raises InsufficientStock instead of letting stock go negative.
        """
        delta = int(delta)
        if delta == 0:
            return
        with transaction.atomic():
            item = cls.objects.select_for_update().get(pk=item_id)
            if item.quantity + delta < 0:
                raise InsufficientStock(
                    f'Not enough stock for {item.name}: '
                    f'{item.quantity} available, {-delta} needed.'
                )
            cls.objects.filter(pk=item_id).update(quantity=F('quantity') + delta)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Items'


class Delivery(models.Model):
    """
    Represents a delivery of an item to a customer.
    """
    item = models.ForeignKey(
        Item, blank=True, null=True, on_delete=models.SET_NULL
    )
    customer_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    location = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateTimeField()
    is_delivered = models.BooleanField(
        default=False, verbose_name='Is Delivered'
    )

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Deliveries'

    def __str__(self):
        return (
            f"Delivery of {self.item} to {self.customer_name} "
            f"at {self.location} on {self.date}"
        )
