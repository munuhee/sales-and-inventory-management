from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from autoslug import AutoSlugField


class Bill(models.Model):
    """A bill owed to an institution, with payment status."""

    slug = AutoSlugField(unique=True, populate_from='institution_name')
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date'
    )
    institution_name = models.CharField(max_length=30)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone number of the institution'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email address of the institution'
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Address of the institution'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Description of the bill'
    )
    payment_details = models.CharField(
        max_length=255,
        help_text='Details of the payment'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Total Amount Owing (Ksh)',
        help_text='Total amount due for payment'
    )
    status = models.BooleanField(
        default=False,
        verbose_name='Paid',
        help_text='Payment status of the bill'
    )

    class Meta:
        ordering = ['status', '-date']

    def __str__(self):
        return self.institution_name
