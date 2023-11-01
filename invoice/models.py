from django.db import models
from store.models import Item
from django_extensions.db.fields import AutoSlugField

class Invoice(models.Model):
    slug = AutoSlugField(unique=True , populate_from='date')
    date = models.DateTimeField(
        auto_now=True,
        blank=False,
        null=False,
        verbose_name=('Date (eg: 2022/11/22 )')
    )
    customer_name = models.CharField(max_length=30, blank=False, null=False)
    contact_number = models.CharField(max_length=13, blank=False, null=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price_per_item = models.FloatField(verbose_name=('Price Per Item (Ksh)'))
    quantity = models.FloatField(default=0.00)
    shipping = models.FloatField(verbose_name=('Shipping and handling'))
    total = models.FloatField(verbose_name=('Total Amount (Ksh)'))
    grand_total = models.FloatField(verbose_name=('Grand total (Ksh)'))

    def save(self, *args, **kwargs):
        quantity = self.quantity
        price_per_item = self.price_per_item
        self.total = quantity * price_per_item
        self.total = round(self.total, 2)
        self.grand_total = self.total + self.shipping
        self.grand_total = round(self.grand_total, 2)

        return super(Invoice, self).save()

    def __str__(self):
        return self.slug

