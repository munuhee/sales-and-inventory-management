from django.shortcuts import render
from .models import *
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from accounts.models import Profile
from transactions.models import Sale
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import ItemTable, DeliveryTable
from django.db.models import Sum, Avg
from .forms import ProductForm
from functools import reduce
from django.db.models import Q
import operator
from django.db.models import Count

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .filters import ProductFilter

@login_required
def dashboard(request):
    profiles =  Profile.objects.all()
    Category.objects.annotate(nitem=Count('item'))
    items = Item.objects.all()
    total_items = Item.objects.all().aggregate(Sum('quantity')).get('quantity__sum', 0.00)
    items_count = items.count()
    profiles_count = profiles.count()

    #profile pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(profiles, 3)
    try:
        profiles = paginator.page(page)
    except PageNotAnInteger:
        profiles = paginator.page(1)
    except EmptyPage:
        profiles = paginator.page(paginator.num_pages)

    #items pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(items, 4)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items,
        'profiles' : profiles,
        'profiles_count': profiles_count,
        'items_count': items_count,
        'total_items': total_items,
        'vendors' : Vendor.objects.all(),
        'delivery': Delivery.objects.all(),
        'sales': Sale.objects.all()
    }
    return render(request, 'store/dashboard.html', context)
class ProductListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    model = Item
    table_class = ItemTable
    template_name = 'store/productslist.html'
    context_object_name = 'items'
    paginate_by = 10
    SingleTableView.table_pagination = False

class ItemSearchListView(ProductListView):
    paginate_by = 10

    def get_queryset(self):
        result = super(ItemSearchListView, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(operator.and_,
                       (Q(name__icontains=q) for q in query_list))
            )
        return result

class ProductDetailView(LoginRequiredMixin, FormMixin, DetailView):
    model = Item
    template_name = 'store/productdetail.html'

    def get_success_url(self):
        return reverse('product-detail', kwargs={'slug': self.object.slug})

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Item
    template_name = 'store/productcreate.html'
    form_class = ProductForm
    success_url = '/products'

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        #item = Item.objects.get(id=pk)
        if request.POST.get("quantity") < 1:
            return False
        else:
            return True

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    template_name = 'store/productupdate.html'
    fields = ['name','category','quantity','selling_price', 'expiring_date', 'vendor']
    success_url = '/products'

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    template_name = 'store/productdelete.html'
    success_url = '/products'


    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        else:
            return False

# Delivery
class DeliveryListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    model = Delivery
    pagination = 10
    template_name = 'store/deliveries.html'
    context_object_name = 'deliveries'

class DeliverySearchListView(DeliveryListView):
    paginate_by = 10

    def get_queryset(self):
        result = super(DeliverySearchListView, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(operator.and_,
                       (Q(customer_name__icontains=q) for q in query_list))
            )
        return result

class DeliveryDetailView(LoginRequiredMixin, DetailView):
    model = Delivery
    template_name = 'store/deliverydetail.html'
class DeliveryCreateView(LoginRequiredMixin, CreateView):
    model = Delivery
    fields = ['item', 'customer_name', 'phone_number', 'location', 'date','is_delivered']
    template_name = 'store/deliveriescreate.html'
    success_url = '/deliveries'

    def form_valid(self, form):
        return super().form_valid(form)

class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    model = Delivery
    fields = ['item', 'customer_name', 'phone_number', 'location', 'date','is_delivered']
    template_name = 'store/deliveryupdate.html'
    success_url = '/deliveries'

    def form_valid(self, form):
        return super().form_valid(form)


class DeliveryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Delivery
    template_name = 'store/productdelete.html'
    success_url = '/deliveries'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False

