from django.shortcuts import render
from .models import *
from accounts.models import Profile
from transactions.models import Sale
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import ItemTable
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .filters import ProductFilter


def dashboard(request):
    profiles =  Profile.objects.all()
    items = Item.objects.all()
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
        'vendors' : Vendor.objects.all(),
        'delivery': Delivery.objects.all(),
        'sales': Sale.objects.all()
    }
    return render(request, 'store/dashboard.html', context)

    context = {
        'items': items,
        'profile' : profile,
        'profile_count': profile_count,
        'items_count': items_count,
        'vendors' : Vendor.objects.all(),
        'delivery': Delivery.objects.all(),
        'sales': Sale.objects.all()
    }
    return render(request, 'store/dashboard.html', context)

ii
class ProductListView(ExportMixin, tables.SingleTableView):
    model = Item
    table_class = ItemTable
    template_name = 'store/productslist.html'
    context_object_name = 'items'
    paginate_by = 10
    SingleTableView.table_pagination = False

class ProductDetailView(FormMixin, DetailView):
    model = Item
    template_name = 'store/productdetail.html'

    def get_success_url(self):
        return reverse('product-detail', kwargs={'slug': self.object.slug})

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Item
    template_name = 'store/productcreate.html'
    fields = ['name','category','quantity','selling_price', 'expiring_date', 'vendor']
    success_url = '/products'

    def form_valid(self, form):
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    template_name = 'store/productupdate.html'
    fields = ['name','category','quantity','selling_price', 'expiring_date', 'vendor']

    def form_valid(self, form):
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    template_name = 'store/productdelete.html'
    success_url = '/products'

    def test_func(self):
        item = self.get_object()