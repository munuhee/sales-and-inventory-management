import django_tables2 as tables

from .models import Sale, Purchase


class SaleTable(tables.Table):
    class Meta:
        model = Sale
        fields = (
            'id', 'date_added', 'customer', 'sub_total', 'discount_amount',
            'tax_amount', 'grand_total', 'amount_paid', 'amount_change', 'status',
        )


class PurchaseTable(tables.Table):
    class Meta:
        model = Purchase
        fields = (
            'item', 'vendor', 'order_date', 'delivery_date', 'quantity',
            'delivery_status', 'price', 'total_value',
        )
