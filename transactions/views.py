from django.shortcuts import render
from .models import *
from django.contrib.auth.models import User
from .filters import PurchaseFilter, SaleFilter
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import PurchaseTable, SaleTable
from django.core.exceptions import ValidationError
from accounts.models import Profile
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
    context_object_name = 'purchases'
    paginate_by = 10
    SingleTableView.table_pagination = False

class PurchaseDetailView(FormMixin, DetailView):
    model = Purchase
    template_name = 'transactions/sale_detail.html'

    def get_success_url(self):
        return reverse('sale-detail', kwargs={'slug': self.object.slug})

class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = Purchase
    template_name = 'transactions/purchasescreate.html'
    fields = ['item', 'description', 'vendor', 'order_date', 'delivery_date', 'quantity', 'price', 'delivery_status']

    def form_valid(self, form):
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('purchaseslist')

class PurchaseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Purchase
    template_name = 'transactions/purchaseupdate.html'
    fields = ['item', 'description', 'vendor', 'order_date', 'delivery_date', 'quantity', 'price', 'delivery_status']

    def form_valid(self, form):
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('purchase-update')
    def test_func(self):
        profiles = Profile.objects.all()
        if self.request.user.profile in profiles:
            return True
        else:
            return False
    def get_success_url(self):
            return reverse('purchaseslist')


class PurchaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Purchase
    template_name = 'transactions/purchasedelete.html'

    def test_func(self):
        profiles = Profile.objects.all()
        if self.request.user.profile in profiles:
            return True
        else:
            return False
    def get_success_url(self):
            return reverse('purchaseslist')

#Sales Order
class SaleListView(ExportMixin, tables.SingleTableView):
    model = Sale
    table_class = SaleTable
    template_name = 'transactions/sales_list.html'
    context_object_name = 'sales'
    paginate_by = 10
    SingleTableView.table_pagination = False

class SaleDetailView(DetailView):
    model = Sale
    template_name = 'transactions/saledetail.html'


class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = 'transactions/salescreate.html'
    fields = ['item', 'customer_name', 'payment_method', 'quantity', 'price', 'amount_received']

    def get_success_url(self):
        return reverse('saleslist')

    def form_valid(self, form):
        # Check if the product is available in stock
        item = form.cleaned_data['item']
        quantity = form.cleaned_data['quantity']

        if item.quantity < quantity:
            raise ValidationError(f"Only {item.quantity} units of '{item.name}' are available.")

        form.instance.profile = self.request.user.profile
        return super().form_valid(form)

    def test_func(self):
        profile_list = Profile.objects.all()
        if self.request.user.profile in profile_list:
            return False
        else:
            return True

class SaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sale
    template_name = 'transactions/sale_update.html'
    fields = ['item', 'customer_name', 'payment_method', 'quantity', 'price', 'amount_received']

    def test_func(self):
        profiles = Profile.objects.all()
        if self.request.user.profile in profiles:
            return True
        else:
            return False

    def get_success_url(self):
        return reverse('saleslist')

    def form_valid(self, form):
        form.instance.profile = self.request.user.profile
        return super().form_valid(form)

class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = 'transactions/saledelete.html'

    def get_success_url(self):
        return reverse('saleslist')

    def test_func(self):
        purchase = self.get_object()

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False