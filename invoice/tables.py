import django_tables2 as tables

from .models import Invoice


class InvoiceTable(tables.Table):
    class Meta:
        model = Invoice
        fields = (
            'date', 'customer_name', 'contact_number', 'item',
            'price_per_item', 'quantity', 'shipping', 'total', 'grand_total',
        )
