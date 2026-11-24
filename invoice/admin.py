from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    fields = ('customer_name', 'contact_number', 'item', 'price_per_item', 'quantity', 'shipping')
    list_display = (
        'invoice_number', 'date', 'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping', 'total', 'grand_total',
    )
    list_select_related = ('item',)
    search_fields = ('customer_name', 'contact_number')
