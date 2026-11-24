"""
Store views: dashboard, products, categories and deliveries.
"""
from datetime import timedelta

from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Value, DecimalField, F
from django.db.models.functions import Coalesce, TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django_tables2 import SingleTableMixin
from django_tables2.export.views import ExportMixin

from accounts.models import Profile, Vendor
from accounts.permissions import (
    ManagerRequiredMixin, RoleRequiredMixin, is_manager, role_required, OPERATIVE,
)
from transactions.models import Sale
from .forms import ItemForm, CategoryForm, DeliveryForm
from .mixins import ProtectedDeleteMixin, SearchMixin
from .models import Category, Item, Delivery
from .tables import ItemTable, DeliveryTable

LOW_STOCK_THRESHOLD = 5


class ManagerExportMixin(ExportMixin):
    """Table export (``?_export=xlsx``) restricted to managers."""

    export_formats = ('xlsx', 'csv')

    def get(self, request, *args, **kwargs):
        if self.export_trigger_param in request.GET and not is_manager(request.user):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)


@role_required(OPERATIVE)
def dashboard(request):
    now = timezone.localtime()
    today = now.date()
    month_start = today.replace(day=1)
    completed = Sale.objects.filter(status=Sale.STATUS_COMPLETED)
    money = DecimalField(max_digits=14, decimal_places=2)

    def revenue(qs):
        return qs.aggregate(total=Coalesce(Sum('grand_total'), Value(0), output_field=money))['total']

    category_rows = (
        Category.objects.annotate(item_count=Count('item')).order_by('-item_count', 'name')
        .values('name', 'item_count')[:12]
    )
    since = today - timedelta(days=29)
    daily = {
        row['day']: float(row['total'])
        for row in completed.filter(date_added__date__gte=since)
        .annotate(day=TruncDate('date_added'))
        .values('day')
        .annotate(total=Sum('grand_total'))
    }
    days = [since + timedelta(days=offset) for offset in range(30)]

    context = {
        'products_count': Item.objects.count(),
        'units_in_stock': Item.objects.aggregate(total=Coalesce(Sum('quantity'), 0))['total'],
        'stock_value': Item.objects.aggregate(
            total=Coalesce(Sum(F('quantity') * F('price'), output_field=money), Value(0), output_field=money)
        )['total'],
        'profiles_count': Profile.objects.filter(status='A').count(),
        'vendors_count': Vendor.objects.count(),
        'pending_deliveries': Delivery.objects.filter(is_delivered=False).count(),
        'sales_today': completed.filter(date_added__date=today).count(),
        'revenue_today': revenue(completed.filter(date_added__date=today)),
        'revenue_month': revenue(completed.filter(date_added__date__gte=month_start)),
        'low_stock': Item.objects.filter(quantity__lte=LOW_STOCK_THRESHOLD)
        .select_related('category').order_by('quantity', 'name')[:8],
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'recent_sales': Sale.objects.select_related('customer').order_by('-date_added')[:6],
        'chart_data': {
            'categories': [row['name'] for row in category_rows],
            'category_counts': [row['item_count'] for row in category_rows],
            'sale_labels': [day.strftime('%d %b') for day in days],
            'sale_values': [daily.get(day, 0) for day in days],
        },
    }
    return render(request, "store/dashboard.html", context)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
class ProductListView(RoleRequiredMixin, SearchMixin, ManagerExportMixin, SingleTableMixin, ListView):
    model = Item
    table_class = ItemTable
    template_name = "store/productslist.html"
    context_object_name = "items"
    paginate_by = 20
    table_pagination = False
    export_name = 'products'
    search_fields = ('name', 'category__name', 'vendor__name')

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'vendor')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['low_stock_threshold'] = LOW_STOCK_THRESHOLD
        return context


class ItemSearchListView(ProductListView):
    """Kept for old links: /search/?q= behaves like the products list."""


class ProductDetailView(RoleRequiredMixin, DetailView):
    model = Item
    template_name = "store/productdetail.html"

    def get_queryset(self):
        return Item.objects.select_related('category', 'vendor')


class ProductCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Item
    template_name = "store/productcreate.html"
    form_class = ItemForm
    success_url = reverse_lazy('productslist')
    success_message = '%(name)s added.'


class ProductUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Item
    template_name = "store/productupdate.html"
    form_class = ItemForm
    success_url = reverse_lazy('productslist')
    success_message = '%(name)s updated.'


class ProductDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Item
    template_name = "store/productdelete.html"
    success_url = reverse_lazy('productslist')
    success_message = 'Product deleted.'
    protected_message = (
        'This product has sales, purchases or invoices, so it cannot be deleted. '
        'Set its quantity to zero instead.'
    )


# ---------------------------------------------------------------------------
# Deliveries
# ---------------------------------------------------------------------------
class DeliveryListView(RoleRequiredMixin, SearchMixin, ManagerExportMixin, SingleTableMixin, ListView):
    model = Delivery
    table_class = DeliveryTable
    template_name = "store/deliveries.html"
    context_object_name = "deliveries"
    paginate_by = 20
    table_pagination = False
    export_name = 'deliveries'
    search_fields = ('customer_name', 'location', 'item__name')

    def get_queryset(self):
        return super().get_queryset().select_related('item')


class DeliverySearchListView(DeliveryListView):
    pass


class DeliveryDetailView(RoleRequiredMixin, DetailView):
    model = Delivery
    template_name = "store/deliverydetail.html"


class DeliveryCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = reverse_lazy('deliveries')
    success_message = 'Delivery scheduled.'


class DeliveryUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = reverse_lazy('deliveries')
    success_message = 'Delivery updated.'


class DeliveryDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Delivery
    template_name = "store/deliverydelete.html"
    success_url = reverse_lazy('deliveries')
    success_message = 'Delivery deleted.'


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
class CategoryListView(RoleRequiredMixin, SearchMixin, ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    search_fields = ('name',)

    def get_queryset(self):
        return super().get_queryset().annotate(item_count=Count('item')).order_by('name')


class CategoryDetailView(RoleRequiredMixin, DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.item_set.select_related('vendor')[:50]
        return context


class CategoryCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    success_message = 'Category %(name)s created.'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    success_message = 'Category %(name)s updated.'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Category
    template_name = 'store/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('category-list')
    success_message = 'Category deleted.'
    protected_message = 'This category still has products. Move or delete them first.'


# ---------------------------------------------------------------------------
# Point of sale item search
# ---------------------------------------------------------------------------
@require_GET
@role_required(OPERATIVE)
def get_items_ajax_view(request):
    term = (request.GET.get('term') or '').strip()[:50]
    items = Item.objects.select_related('category').filter(quantity__gt=0)
    if term:
        items = items.filter(name__icontains=term)
    return JsonResponse([item.to_json() for item in items.order_by('name')[:20]], safe=False)
