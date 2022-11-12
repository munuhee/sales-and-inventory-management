from django.contrib import admin

# Register your models here.
from .models import *


@admin.register(Profile)
class StatisticDiff(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'email', 'role', 'status')

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    fields = ('name', 'phone_number', 'address')
    list_display = ('name', 'phone_number', 'address')
    search_fields = ['name', 'phone_number', 'address']