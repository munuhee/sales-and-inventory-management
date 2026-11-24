import django_tables2 as tables

from .models import Item, Delivery


class ItemTable(tables.Table):
    """Used for the products export."""

    class Meta:
        model = Item
        fields = ('id', 'name', 'category', 'quantity', 'price', 'expiring_date', 'vendor')


class DeliveryTable(tables.Table):
    """Used for the deliveries export."""

    class Meta:
        model = Delivery
        fields = ('id', 'item', 'customer_name', 'phone_number', 'location', 'date', 'is_delivered')
