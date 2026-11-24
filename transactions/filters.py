import django_filters

from .models import Sale, Purchase


class SaleFilter(django_filters.FilterSet):
    class Meta:
        model = Sale
        fields = ['customer', 'status', 'served_by']


class PurchaseFilter(django_filters.FilterSet):
    class Meta:
        model = Purchase
        fields = ['item', 'vendor', 'delivery_status']
