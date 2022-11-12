from django.shortcuts import render
from .models import *
from .filters import PurchaseFilter, SaleFilter
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import PurchaseTable, SaleTable
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

# Create your views here.
class PurchaseListView(ExportMixin, tables.SingleTableView):
    model = Purchase
    table_class = SaleTable
    template_name = 'transactions/purchases_list.html'
    context_object_name = 'sales'
    paginate_by = 10
    SingleTableView.table_pagination = False

class PurchaseDetailView(FormMixin, DetailView):
    model = Purchase
    template_name = 'transactions/sale_detail.html'

    def get_success_url(self):
        return reverse('sale-detail', kwargs={'slug': self.object.slug})

class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = Purchase
    template_name = 'transactions/purchase_create.html'
    fields = ['name','category','quantity','selling_price', 'expiring_date', 'vendor']
    success_url = '/sales'

    def form_valid(self, form):
        return super().form_valid(form)

class PurchaseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Purchase
    template_name = 'transactions/purchase_update.html'
    fields = ['name','category','quantity','selling_price', 'expiring_date', 'vendor']

    def form_valid(self, form):
        return super().form_valid(form)


class PurchaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Purchase
    template_name = 'transactions/purchase_delete.html'
    success_url = '/purchases'

    def test_func(self):
        purchase = self.get_object()

#Sales Order
class SaleListView(ExportMixin, tables.SingleTableView):
    model = Sale
    table_class = SaleTable
    template_name = 'transactions/sales_list.html'
    context_object_name = 'sales'
    paginate_by = 10
    SingleTableView.table_pagination = False

class SaleDetailView(FormMixin, DetailView):
    model = Sale
    template_name = 'transactions/sale_detail.html'

    def get_success_url(self):
        return reverse('sale-detail', kwargs={'slug': self.object.slug})

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = 'transactions/sale_create.html'
    fields = ['item', 'description', 'vendor', 'delivery_date', 'quantity', 'price']
    success_url = '/sales'

    def form_valid(self, form):
        return super().form_valid(form)

class SaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sale
    template_name = 'transactions/sale_update.html'
    fields = ['item', 'description', 'vendor', 'delivery_date', 'quantity', 'price']

    def form_valid(self, form):
        return super().form_valid(form)


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = 'transactions/sale_delete.html'
    success_url = '/sales'

    def test_func(self):
        purchase = self.get_object()