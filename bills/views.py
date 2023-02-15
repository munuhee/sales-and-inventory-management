from django.shortcuts import render
from .models import *
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import BillTable
from accounts.models import Profile
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

class BillListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    model = Bill
    table_class = BillTable
    template_name = 'bills/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 10
    SingleTableView.table_pagination = False

''' class BillDetailView(FormMixin, DetailView):
    model = Bill
    template_name = 'bills/billdetail.html'

    def get_success_url(self):
        return reverse('bill-detail', kwargs={'slug': self.object.slug})
 '''
class BillCreateView(LoginRequiredMixin, CreateView):
    model = Bill
    template_name = 'bills/billcreate.html'
    fields = ['date','institution_name', 'phone_number','email','address','description', 'payment_details', 'amount','status']
    success_url = '/bills'

    def form_valid(self, form):
        return super().form_valid(form)

class BillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Bill
    template_name = 'bills/billupdate.html'
    fields = ['date','institution_name', 'phone_number','email','address','description', 'payment_details', 'amount','status']

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        profiles = Profile.objects.all()
        if self.request.user.profile in profiles:
            return True
        else:
            return False

    def get_success_url(self):
        return reverse('bill_list')

class BillDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Bill
    template_name = 'bill/billdelete.html'


    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False
    def get_success_url(self):

        return reverse('bill_list')
