from django.db import models
from store.models import Item
from accounts.models import *
from django_extensions.db.fields import AutoSlugField

# Create your models here.

PAYMENT_CHOICES = [
    ('MP', 'MPESA'),
    ('VISA', 'VISA'),
    ('CS', 'CASH'),
    ('VM', 'VOOMA'),
    ('BK', 'BANK')
]

DELIVERY_CHOICES = [
    ('P', 'PENDING'),
    ('S', 'SUCCESSFUL')
]

class Sale(models.Model):
    slug = AutoSlugField(unique=True , populate_from='customer_name')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    customer_name = models.CharField(max_length=20, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    quantity = models.FloatField(default=0.00, blank=False, null=False)
    payment_method = models.CharField(choices=PAYMENT_CHOICES, max_length=20, blank='True', null=True)
    price = models.FloatField(default=0.00, blank=False, null=False)
    total_value = models.FloatField(blank=True, null=True)
    amount_received = models.FloatField(default=False, blank=False, null=False)
    balance = models.FloatField(default=False, blank=False, null=False)
    profile = models.ForeignKey(Profile, verbose_name=('Served by'), on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        amt_received = self.amount_received
        balance = self.balance
        price = self.price
        quantity = self.quantity
        self.total_value = price * quantity
        self.balance = amt_received - self.total_value
        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.item.name)

class Purchase(models.Model):
    slug = AutoSlugField(unique=True , populate_from='vendor')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    description = models.TextField(max_length=300, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, related_name='vendor', on_delete=models.CASCADE, blank=False, null=False)
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name=('Delivery Date'))
    quantity = models.FloatField(default=0.00, blank=False, null=False)
    delivery_status = models.CharField(choices=DELIVERY_CHOICES, max_length=3, default='P', blank=False, null=False, verbose_name=('Delivery Status'))
    price = models.FloatField(default=0.00, blank=False, null=False, verbose_name=('Price per item(Ksh)'))
    total_value = models.FloatField()

    def save(self, *args, new_name=True, **kwargs):
        quantity = self.quantity
        price = self.price
        self.total_value = price * quantity
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.item.name

    class Meta:
        ordering = ["order_date"]
