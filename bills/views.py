from django.shortcuts import render
from .models import Bill
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from .tables import BillTable
from accounts.models import Profile
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)

class BillListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    model = Bill
    table_class = BillTable
    template_name = 'bills/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 10
    SingleTableView.table_pagination = False

class BillCreateView(LoginRequiredMixin, CreateView):
    model = Bill
    template_name = 'bills/billcreate.html'
    fields = ['institution_name', 'phone_number', 'email', 'address', 'description', 'payment_details', 'amount', 'status']
    success_url = '/bills'

class BillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Bill
    template_name = 'bills/billupdate.html'
    fields = ['institution_name', 'phone_number', 'email', 'address', 'description', 'payment_details', 'amount', 'status']

    def test_func(self):
        return self.request.user.profile in Profile.objects.all()

    def get_success_url(self):
        return reverse('bill_list')

class BillDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Bill
    template_name = 'bills/billdelete.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        return reverse('bill_list')
