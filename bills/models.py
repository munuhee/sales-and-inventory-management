from django.db import models
from autoslug import AutoSlugField

class Bill(models.Model):
    slug = AutoSlugField(unique=True, populate_from='date')
    date = models.DateTimeField(auto_now_add=True, verbose_name=('Date (eg: 2022/11/22)'))
    institution_name = models.CharField(max_length=30, blank=False, null=False)
    phone_number = models.IntegerField(blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    payment_details = models.CharField(max_length=255, blank=False, null=False)
    amount = models.FloatField(verbose_name=('Total Amount Owing (Ksh)'))
    status = models.BooleanField(default=False, verbose_name=('Paid'))

    def __str__(self):
        return self.institution_name
