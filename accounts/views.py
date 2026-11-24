from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from store.mixins import ProtectedDeleteMixin, SearchMixin
from .forms import (
    CreateUserForm, CustomerForm, LoginForm, LoyaltyAdjustmentForm,
    ProfileUpdateForm, StaffCreateForm, StaffUpdateForm, UserUpdateForm, VendorForm,
)
from .models import Customer, Profile, Vendor
from .permissions import (
    AdminRequiredMixin, ManagerRequiredMixin, RoleRequiredMixin,
    is_manager, role_required, EXECUTIVE, OPERATIVE,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allow_registration'] = settings.ALLOW_REGISTRATION
        return context


def register(request):
    """
    Self sign-up. The new account is created Inactive and cannot sign in
    until an admin approves it from the staff page.
    """
    if not settings.ALLOW_REGISTRATION:
        raise Http404
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Account created. An administrator needs to approve it before you can sign in.'
            )
            return redirect('user-login')
    else:
        form = CreateUserForm()
    return render(request, 'accounts/register.html', {'form': form})


@role_required(OPERATIVE)
def profile(request):
    return render(request, 'accounts/profile.html')


@role_required(OPERATIVE)
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('user-profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'accounts/profile_update.html', {'u_form': u_form, 'p_form': p_form})


# ---------------------------------------------------------------------------
# Staff (admins only)
# ---------------------------------------------------------------------------
class ProfileListView(AdminRequiredMixin, SearchMixin, ListView):
    model = Profile
    template_name = 'accounts/stafflist.html'
    context_object_name = 'profiles'
    paginate_by = 20
    search_fields = ('user__username', 'first_name', 'last_name', 'email')

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        if self.request.GET.get('pending') == '1':
            queryset = queryset.filter(status='INA')
        return queryset.order_by('status', 'user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = Profile.objects.filter(status='INA').count()
        return context


class ProfileCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = StaffCreateForm
    template_name = 'accounts/staffcreate.html'
    success_url = reverse_lazy('profile_list')
    success_message = 'Staff account %(username)s created.'


class ProfileUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = StaffUpdateForm
    template_name = 'accounts/staffupdate.html'
    success_url = reverse_lazy('profile_list')
    success_message = 'Staff member updated.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['acting_user'] = self.request.user
        return kwargs


@role_required('AD')
def profile_approve(request, pk):
    """One click approval for a pending sign-up."""
    if request.method != 'POST':
        raise Http404
    target = get_object_or_404(Profile.objects.select_related('user'), pk=pk)
    target.status = 'A'
    target.save(update_fields=['status'])
    messages.success(request, f'{target.user.username} can now sign in as {target.get_role_display()}.')
    return redirect('profile_list')


class ProfileDeleteView(AdminRequiredMixin, DeleteView):
    """Deletes the staff member's user account (and its profile)."""

    model = Profile
    template_name = 'accounts/staffdelete.html'
    success_url = reverse_lazy('profile_list')

    def get_object(self, queryset=None):
        target = super().get_object(queryset)
        if target.user_id == self.request.user.pk:
            raise PermissionDenied('You cannot delete your own account.')
        if target.user.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied('Only a superuser can delete a superuser.')
        return target

    def form_valid(self, form):
        username = self.object.user.username
        User.objects.filter(pk=self.object.user_id).delete()
        messages.success(self.request, f'Staff account {username} deleted.')
        return redirect(self.success_url)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
class CustomerListView(RoleRequiredMixin, SearchMixin, ListView):
    model = Customer
    template_name = 'accounts/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    search_fields = ('first_name', 'last_name', 'phone', 'email')


class CustomerDetailView(RoleRequiredMixin, DetailView):
    model = Customer
    template_name = 'accounts/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ledger'] = self.object.loyalty_transactions.select_related('sale', 'created_by')[:50]
        context['recent_sales'] = self.object.sale_set.order_by('-date_added')[:10]
        if is_manager(self.request.user):
            context['adjust_form'] = kwargs.get('adjust_form') or LoyaltyAdjustmentForm()
        return context


@role_required(EXECUTIVE)
def customer_loyalty_adjust(request, pk):
    """Manager correction of points. Always recorded in the ledger."""
    from transactions.loyalty import apply_points
    from transactions.models import LoyaltyTransaction

    customer = get_object_or_404(Customer, pk=pk)
    if request.method != 'POST':
        return redirect('customer_detail', pk=pk)
    form = LoyaltyAdjustmentForm(request.POST)
    if form.is_valid():
        try:
            apply_points(
                customer.pk, form.cleaned_data['points'], LoyaltyTransaction.ADJUST,
                user=request.user, note=form.cleaned_data['note'],
            )
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, 'Loyalty points adjusted.')
        return redirect('customer_detail', pk=pk)
    view = CustomerDetailView()
    view.setup(request, pk=pk)
    view.object = customer
    return render(request, view.template_name, view.get_context_data(object=customer, adjust_form=form))


class CustomerCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')
    success_message = 'Customer %(first_name)s added.'


class CustomerUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')
    success_message = 'Customer updated.'


class CustomerDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Customer
    template_name = 'accounts/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    success_message = 'Customer deleted.'
    protected_message = 'This customer has sales on record and cannot be deleted.'


@require_GET
@role_required(OPERATIVE)
def get_customers(request):
    """Customer search for the till (Select2 format)."""
    term = (request.GET.get('term') or '').strip()[:50]
    customers = Customer.objects.all()
    if term:
        customers = customers.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(phone__icontains=term)
        )
    return JsonResponse({'results': [c.to_select2() for c in customers[:20]]})


# ---------------------------------------------------------------------------
# Vendors (managers)
# ---------------------------------------------------------------------------
class VendorListView(ManagerRequiredMixin, SearchMixin, ListView):
    model = Vendor
    template_name = 'accounts/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20
    search_fields = ('name', 'phone_number', 'address')


class VendorCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')
    success_message = 'Vendor %(name)s added.'


class VendorUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')
    success_message = 'Vendor updated.'


class VendorDeleteView(ManagerRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Vendor
    template_name = 'accounts/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor-list')
    success_message = 'Vendor deleted.'
    protected_message = 'This vendor has purchase orders and cannot be deleted.'
