import django_tables2 as tables
from .models import Invoice
from django.shortcuts import render

class InvoiceTable(tables.Table):
    class Meta:
        model = Invoice
        template_name = "django_tables2/semantic.html"
        fields = ('date','customer_name','contact_number','item','price_per_item','quantity', 'total')
        order_by_field = 'sort'
