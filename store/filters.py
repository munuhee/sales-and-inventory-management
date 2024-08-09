import django_filters
from .models import Item


class ProductFilter(django_filters.FilterSet):
    """
    Filter set for Item model.
    """
    class Meta:
        model = Item
        fields = ['name', 'category', 'vendor']
