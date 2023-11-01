import django_filters
from .models import Item

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Item
        fields = ['name', 'category', 'vendor']
