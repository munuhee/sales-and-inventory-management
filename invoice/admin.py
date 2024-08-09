from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the Invoice model.
    """
    fields = (
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity'
    )
    list_display = (
        'date', 'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping', 'total',
        'grand_total'
    )
