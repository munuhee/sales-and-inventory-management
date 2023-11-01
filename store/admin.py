from django.contrib import admin
from .models import Category, Delivery, Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    fields = ('name', 'category','quantity','selling_price', 'expiring_date', 'vendor')
    list_display = ('id', 'name','category', 'quantity', 'selling_price', 'expiring_date', 'vendor')
    search_fields = ['id', 'name']

admin.site.register(Category)
admin.site.register(Delivery)
