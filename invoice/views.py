from django import forms
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.permissions import ManagerRequiredMixin, RoleRequiredMixin, role_required, OPERATIVE
from InventoryMS.pdf import render_pdf_response
from store.mixins import ProtectedDeleteMixin, SearchMixin
from .models import Invoice

INVOICE_FIELDS = ['customer_name', 'contact_number', 'item', 'price_per_item', 'quantity', 'shipping']


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = INVOICE_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class InvoiceListView(RoleRequiredMixin, SearchMixin, ListView):
    model = Invoice
    template_name = 'invoice/invoicelist.html'
    context_object_name = 'invoices'
    paginate_by = 20
    search_fields = ('customer_name', 'contact_number', 'item__name')

    def get_queryset(self):
        return super().get_queryset().select_related('item')


class InvoiceDetailView(RoleRequiredMixin, DetailView):
    """Invoice summary. The printable invoice is the PDF."""
    model = Invoice
    template_name = 'invoice/invoicedetail.html'

    def get_queryset(self):
        return Invoice.objects.select_related('item', 'item__category')


@role_required(OPERATIVE)
def invoice_pdf(request, slug):
    """Invoice as PDF: inline for printing, ?download=1 to save it."""
    invoice = get_object_or_404(Invoice.objects.select_related('item', 'item__category'), slug=slug)
    context = {'invoice': invoice, 'business': settings.BUSINESS, 'printed_at': timezone.now()}
    return render_pdf_response(
        'documents/invoice.html', context,
        filename=f'invoice-{invoice.invoice_number}.pdf',
        request=request,
        download=request.GET.get('download') == '1',
    )


class InvoiceCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoice/invoicecreate.html'
    success_message = 'Invoice created.'

    def get_success_url(self):
        return self.object.get_absolute_url()


class InvoiceUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoice/invoiceupdate.html'
    success_message = 'Invoice updated.'

    def get_success_url(self):
        return self.object.get_absolute_url()


class InvoiceDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Invoice
    template_name = 'invoice/invoicedelete.html'
    success_url = reverse_lazy('invoicelist')
    success_message = 'Invoice deleted.'
