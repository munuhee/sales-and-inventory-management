from django.db import models
from store.models import Item
from django_extensions.db.fields import AutoSlugField
# Create your models here.

class Invoice(models.Model):
    slug = AutoSlugField(unique=True , populate_from='date')
    date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=False)
    customer_name = models.CharField(max_length=30, blank=False, null=False)
    contact_number = models.CharField(max_length=13, blank=False, null=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price_per_item = models.FloatField(verbose_name=('Price Per Iem (Ksh)'))
    quantity = models.FloatField(default=0.00)
    total = models.FloatField(verbose_name=('Total Amount (Ksh)'))

    def save(self, *args, new_name=True, **kwargs):
        quantity = self.quantity
        price_per_item = self.price_per_item
        self.total = quantity * price_per_item
        self.total = round(self.total, 2)
        return super(Invoice, self).save()

    def __str__(self):
        return self.slug

