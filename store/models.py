from django.db import models
from datetime import date
from django.urls import reverse
from django.utils.text import slugify
from accounts.models import *
from django_extensions.db.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField

class Category(models.Model):
	name = models.CharField(max_length=50)
	slug = AutoSlugField(unique=True , populate_from='name')
	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = 'Categories'

class Item(models.Model):
	slug = AutoSlugField(unique=True , populate_from='name')
	name = models.CharField(max_length=50, blank=False, null=False)
	category = models.ForeignKey(Category,on_delete=models.CASCADE)
	quantity= models.FloatField(default=0.00)
	selling_price = models.FloatField(default=0)
	expiring_date = models.DateTimeField(null=True, blank=True)
	vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)




	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('item-detail', kwargs={'slug': self.slug})

	class Meta:
		ordering = ["name"]
		verbose_name_plural = "Items"

class Delivery(models.Model):
    item = models.ForeignKey(Item, blank=True, null=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(blank=True, null=True, max_length=30)
    phone_number = PhoneNumberField(null=True,blank=True)
    location = models.CharField(blank=True, null=True, max_length=20)
    date = models.DateTimeField(null=False, blank=False)
    is_delivered = models.BooleanField(default=False, verbose_name=('is-delivered'))