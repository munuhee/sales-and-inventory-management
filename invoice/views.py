# Django core imports
from django.urls import reverse

# Authentication and permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView
)

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Invoice
from .tables import InvoiceTable


class InvoiceListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """
    View for listing invoices with table export functionality.
    """
    model = Invoice
    table_class = InvoiceTable
    template_name = 'invoice/invoicelist.html'
    context_object_name = 'invoices'
    paginate_by = 10
    table_pagination = False  # Disable table pagination


class InvoiceDetailView(DetailView):
    """
    View for displaying invoice details.
    """
    model = Invoice
    template_name = 'invoice/invoicedetail.html'

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful action.
        """
        return reverse('invoice-detail', kwargs={'slug': self.object.pk})


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new invoice.
    """
    model = Invoice
    template_name = 'invoice/invoicecreate.html'
    fields = [
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping'
    ]

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful creation.
        """
        return reverse('invoicelist')


class InvoiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing invoice.
    """
    model = Invoice
    template_name = 'invoice/invoiceupdate.html'
    fields = [
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping'
    ]

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful update.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to update the invoice.
        """
        return self.request.user.is_superuser


class InvoiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting an invoice.
    """
    model = Invoice
    template_name = 'invoice/invoicedelete.html'
    success_url = '/products'  # Can be overridden in get_success_url()

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful deletion.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to delete the invoice.
        """
        return self.request.user.is_superuser
