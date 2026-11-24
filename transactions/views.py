import json
import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from openpyxl import Workbook

from accounts.models import Customer
from accounts.permissions import (
    ManagerRequiredMixin, RoleRequiredMixin, role_required, EXECUTIVE, OPERATIVE,
)
from InventoryMS.pdf import render_pdf_response
from store.mixins import ProtectedDeleteMixin, SearchMixin

from . import loyalty
from .forms import PurchaseForm, VoidSaleForm
from .models import Sale, Purchase
from .services import create_sale, void_sale

logger = logging.getLogger(__name__)

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def _naive(value):
    """Excel cannot store time zones: export local wall clock time."""
    if value is None:
        return None
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.replace(tzinfo=None)


def _xlsx_response(workbook, filename):
    response = HttpResponse(content_type=XLSX)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


# ---------------------------------------------------------------------------
# Exports (managers only: they contain every sale and purchase)
# ---------------------------------------------------------------------------
@role_required(EXECUTIVE)
def export_sales_to_excel(request):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Sales'
    sheet.append([
        'Receipt', 'Date', 'Customer', 'Phone', 'Served by', 'Status',
        'Sub Total', 'Loyalty Discount', 'Tax %', 'Tax Amount', 'Grand Total',
        'Amount Paid', 'Change', 'Points Earned', 'Points Redeemed',
    ])
    sales = Sale.objects.select_related('customer', 'served_by').order_by('date_added')
    for sale in sales.iterator(chunk_size=500):
        sheet.append([
            sale.receipt_number,
            _naive(sale.date_added),
            sale.customer.get_full_name(),
            sale.customer.phone or '',
            sale.served_by.username if sale.served_by else '',
            sale.get_status_display(),
            sale.sub_total,
            sale.discount_amount,
            sale.tax_percentage,
            sale.tax_amount,
            sale.grand_total,
            sale.amount_paid,
            sale.amount_change,
            sale.loyalty_points_earned,
            sale.loyalty_points_redeemed,
        ])
    return _xlsx_response(workbook, 'sales.xlsx')


@role_required(EXECUTIVE)
def export_purchases_to_excel(request):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Purchases'
    sheet.append([
        'ID', 'Item', 'Description', 'Vendor', 'Order Date',
        'Delivery Date', 'Quantity', 'Delivery Status',
        'Price per item', 'Total Value',
    ])
    purchases = Purchase.objects.select_related('item', 'vendor').order_by('order_date')
    for purchase in purchases.iterator(chunk_size=500):
        sheet.append([
            purchase.id,
            purchase.item.name,
            purchase.description or '',
            purchase.vendor.name,
            _naive(purchase.order_date),
            _naive(purchase.delivery_date),
            purchase.quantity,
            purchase.get_delivery_status_display(),
            purchase.price,
            purchase.total_value,
        ])
    return _xlsx_response(workbook, 'purchases.xlsx')


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------
class SaleListView(RoleRequiredMixin, SearchMixin, ListView):
    model = Sale
    template_name = "transactions/sales_list.html"
    context_object_name = "sales"
    paginate_by = 20
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__phone')

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .select_related('customer', 'served_by')
            .annotate(units=Sum('saledetail_set__quantity'), lines=Count('saledetail_set'))
            .order_by('-date_added')
        )
        query = self.get_search_query()
        receipt = query.upper().removeprefix('IMS')
        if receipt.isdigit():
            queryset = Sale.objects.filter(pk=int(receipt)).select_related(
                'customer', 'served_by'
            ).annotate(units=Sum('saledetail_set__quantity'), lines=Count('saledetail_set'))
        return queryset


class SaleDetailView(RoleRequiredMixin, DetailView):
    """Sale summary for staff. The printable receipt is a separate PDF."""

    model = Sale
    template_name = "transactions/saledetail.html"

    def get_queryset(self):
        return Sale.objects.select_related('customer', 'served_by', 'voided_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.saledetail_set.select_related('item', 'item__category')
        context['loyalty_entries'] = self.object.loyalty_transactions.all()
        return context


def receipt_context(sale):
    """Everything the receipt document needs. Reprints always match the original."""
    from django.conf import settings
    from .models import LoyaltyTransaction

    lines = list(sale.saledetail_set.select_related('item', 'item__category'))
    # Balance right after this sale, from the ledger, so a reprint months
    # later still shows what the customer had at the till.
    entry = (
        sale.loyalty_transactions
        .filter(kind__in=[LoyaltyTransaction.EARN, LoyaltyTransaction.REDEEM])
        .order_by('-id').first()
    )
    return {
        'sale': sale,
        'lines': lines,
        'units': sum(line.quantity for line in lines),
        'points_balance': entry.balance_after if entry else None,
        'printed_at': timezone.now(),
        'business': settings.BUSINESS,
    }


@role_required(OPERATIVE)
def sale_receipt_pdf(request, pk):
    """Receipt as PDF: inline for printing, ?download=1 to save it."""
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'served_by', 'served_by__profile'), pk=pk
    )
    context = receipt_context(sale)
    return render_pdf_response(
        'documents/receipt.html', context,
        filename=f'receipt-{sale.receipt_number}.pdf',
        request=request,
        download=request.GET.get('download') == '1',
    )


def _bad_request(message, status=400):
    return JsonResponse({'status': 'error', 'message': message}, status=status)


@role_required(OPERATIVE)
def sale_create_view(request):
    """
    Point of sale. GET renders the till; POST takes JSON:
        {customer, items: [{id, quantity}], tax_percentage, amount_paid,
         redeem_points}
    Everything else is computed on the server.
    """
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return _bad_request('Expected a JSON request.')
        try:
            data = json.loads(request.body or b'{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _bad_request('Invalid JSON in request body.')
        if not isinstance(data, dict):
            return _bad_request('Invalid request.')
        try:
            sale = create_sale(
                user=request.user,
                customer_id=data.get('customer'),
                items=data.get('items'),
                tax_percentage=data.get('tax_percentage', 0),
                amount_paid=data.get('amount_paid', 0),
                redeem_points=data.get('redeem_points', 0),
            )
        except ValidationError as exc:
            return _bad_request(' '.join(exc.messages))
        except Exception:
            logger.exception('Sale creation failed')
            return _bad_request('The sale could not be saved. Please try again.', status=500)

        logger.info('Sale %s created by %s', sale.receipt_number, request.user)
        return JsonResponse({
            'status': 'success',
            'message': f'Sale {sale.receipt_number} completed.',
            'sale_id': sale.pk,
            'receipt_number': sale.receipt_number,
            'grand_total': str(sale.grand_total),
            'change': str(sale.amount_change),
            'points_earned': sale.loyalty_points_earned,
            'redirect': reverse('sale-detail', kwargs={'pk': sale.pk}),
            'receipt_url': reverse('sale-receipt', kwargs={'pk': sale.pk}),
        })

    cfg = loyalty.config()
    context = {
        'active_icon': 'sales',
        'customers': Customer.objects.only('id', 'first_name', 'last_name', 'phone', 'loyalty_points'),
        'loyalty': {
            'enabled': cfg['enabled'],
            'earn_per': str(cfg['earn_per']),
            'point_value': str(cfg['point_value']),
            'min_redeem': cfg['min_redeem'],
        },
    }
    return render(request, "transactions/sale_create.html", context=context)


class SaleVoidView(ManagerRequiredMixin, DetailView):
    """Void a sale: restores stock and reverses loyalty points."""

    model = Sale
    template_name = "transactions/saledelete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', VoidSaleForm())
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VoidSaleForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        try:
            void_sale(self.object, user=request.user, reason=form.cleaned_data['reason'])
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, f'Sale {self.object.receipt_number} voided. Stock restored.')
        return redirect('sale-detail', pk=self.object.pk)


# ---------------------------------------------------------------------------
# Purchases (managers)
# ---------------------------------------------------------------------------
class PurchaseListView(ManagerRequiredMixin, SearchMixin, ListView):
    model = Purchase
    template_name = "transactions/purchases_list.html"
    context_object_name = "purchases"
    paginate_by = 20
    search_fields = ('item__name', 'vendor__name', 'description')

    def get_queryset(self):
        return super().get_queryset().select_related('item', 'vendor')


class PurchaseDetailView(ManagerRequiredMixin, DetailView):
    model = Purchase
    template_name = "transactions/purchasedetail.html"

    def get_queryset(self):
        return Purchase.objects.select_related('item', 'vendor')


class PurchaseFormMixin(SuccessMessageMixin):
    model = Purchase
    form_class = PurchaseForm
    template_name = "transactions/purchases_form.html"
    success_url = reverse_lazy("purchaseslist")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)


class PurchaseCreateView(ManagerRequiredMixin, PurchaseFormMixin, CreateView):
    success_message = 'Purchase order saved.'


class PurchaseUpdateView(ManagerRequiredMixin, PurchaseFormMixin, UpdateView):
    success_message = 'Purchase order updated. Stock adjusted.'


class PurchaseDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Purchase
    template_name = "transactions/purchasedelete.html"
    success_url = reverse_lazy("purchaseslist")
    success_message = 'Purchase order deleted. Any received stock was removed.'
