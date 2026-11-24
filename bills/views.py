from django import forms
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.permissions import ManagerRequiredMixin
from store.mixins import ProtectedDeleteMixin, SearchMixin
from .models import Bill

BILL_FIELDS = [
    'institution_name', 'phone_number', 'email', 'address',
    'description', 'payment_details', 'amount', 'status',
]


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = BILL_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class BillListView(ManagerRequiredMixin, SearchMixin, ListView):
    model = Bill
    template_name = 'bills/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 20
    search_fields = ('institution_name', 'description', 'payment_details')

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status == 'paid':
            queryset = queryset.filter(status=True)
        elif status == 'unpaid':
            queryset = queryset.filter(status=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', '')
        return context


class BillCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Bill
    form_class = BillForm
    template_name = 'bills/billcreate.html'
    success_url = reverse_lazy('bill_list')
    success_message = 'Bill added.'


class BillUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Bill
    form_class = BillForm
    template_name = 'bills/billupdate.html'
    success_url = reverse_lazy('bill_list')
    success_message = 'Bill updated.'


class BillDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Bill
    template_name = 'bills/billdelete.html'
    success_url = reverse_lazy('bill_list')
    success_message = 'Bill deleted.'
