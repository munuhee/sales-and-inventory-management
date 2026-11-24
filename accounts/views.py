from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
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
from .models import (
    Customer, Profile, StaffAuditLog, Vendor, STATUS_CHOICES, ROLE_CHOICES,
)
from .permissions import (
    ManagerRequiredMixin, RoleRequiredMixin, StaffCreateRequiredMixin,
    StaffDeleteRequiredMixin, StaffUpdateRequiredMixin, StaffViewRequiredMixin,
    capability_required, is_manager, role_required, EXECUTIVE, OPERATIVE,
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
            user = form.save()
            user.profile.status = 'PEN'
            user.profile.save(update_fields=['status'])
            StaffAuditLog.objects.create(
                actor_username='Self sign-up',
                target_user=user,
                target_username=user.get_username(),
                action=StaffAuditLog.CREATED,
                new_role=user.profile.role,
                new_status=user.profile.status,
                new_login_enabled=False,
            )
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
            user = u_form.save()
            profile = p_form.save()
            user.email = profile.email or ''
            user.save(update_fields=['email'])
            messages.success(request, 'Profile updated.')
            return redirect('user-profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'accounts/profile_update.html', {'u_form': u_form, 'p_form': p_form})


# ---------------------------------------------------------------------------
# Staff (admins only)
# ---------------------------------------------------------------------------
class ProfileListView(StaffViewRequiredMixin, SearchMixin, ListView):
    model = Profile
    template_name = 'accounts/stafflist.html'
    context_object_name = 'profiles'
    paginate_by = 20
    search_fields = ('user__username', 'first_name', 'last_name', 'email')

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        status = self.request.GET.get('status', '').strip()
        role = self.request.GET.get('role', '').strip()
        if self.request.GET.get('pending') == '1':
            status = 'PEN'
        if status == 'BLOCKED':
            queryset = queryset.filter(
                Q(status__in=['INA', 'OL']) | Q(user__is_active=False)
            )
        elif status == 'DISABLED':
            queryset = queryset.filter(user__is_active=False)
        elif status in {'PEN', 'A', 'INA', 'OL'}:
            queryset = queryset.filter(status=status)
        if role in {'OP', 'EX', 'AD'}:
            queryset = queryset.filter(role=role)
        return queryset.order_by('status', 'user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = Profile.objects.filter(status='PEN').count()
        context['active_count'] = Profile.objects.filter(
            status='A', user__is_active=True
        ).count()
        context['inactive_count'] = Profile.objects.filter(
            Q(status__in=['INA', 'OL']) | Q(user__is_active=False)
        ).distinct().count()
        context['staff_count'] = Profile.objects.count()
        context['audit_events'] = StaffAuditLog.objects.select_related('actor')[:8]
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_role'] = self.request.GET.get('role', '')
        context['status_options'] = list(STATUS_CHOICES) + [
            ('DISABLED', 'Login disabled'),
            ('BLOCKED', 'Inactive or on leave')
        ]
        context['role_options'] = ROLE_CHOICES
        return context


class ProfileCreateView(StaffCreateRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = StaffCreateForm
    template_name = 'accounts/staffcreate.html'
    success_url = reverse_lazy('profile_list')
    success_message = 'Staff account %(username)s created.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['acting_user'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.object.profile
        StaffAuditLog.objects.create(
            actor=self.request.user,
            actor_username=self.request.user.get_username(),
            target_user=self.object,
            target_username=self.object.get_username(),
            action=StaffAuditLog.CREATED,
            new_role=profile.role,
            new_status=profile.status,
            new_login_enabled=self.object.is_active and profile.status == 'A',
        )
        return response


class ProfileUpdateView(StaffUpdateRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = StaffUpdateForm
    template_name = 'accounts/staffupdate.html'
    success_url = reverse_lazy('profile_list')
    success_message = 'Staff member updated.'

    def get_object(self, queryset=None):
        target = super().get_object(queryset)
        if not self.request.user.is_superuser and (
            target.user.is_superuser or target.role == 'AD'
        ):
            raise PermissionDenied('Only a superuser can modify an Admin account.')
        return target

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['acting_user'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        old_role = self.object.role
        old_status = self.object.status
        old_login_enabled = self.object.user.is_active and old_status == 'A'
        response = super().form_valid(form)
        new_login_enabled = self.object.user.is_active and self.object.status == 'A'
        if (old_role, old_status, old_login_enabled) != (
            self.object.role, self.object.status, new_login_enabled
        ):
            StaffAuditLog.objects.create(
                actor=self.request.user,
                actor_username=self.request.user.get_username(),
                target_user=self.object.user,
                target_username=self.object.user.get_username(),
                action=StaffAuditLog.UPDATED,
                previous_role=old_role,
                new_role=self.object.role,
                previous_status=old_status,
                new_status=self.object.status,
                previous_login_enabled=old_login_enabled,
                new_login_enabled=new_login_enabled,
            )
        return response


@capability_required('staff.approve')
def profile_approve(request, pk):
    """One click approval for a pending sign-up."""
    if request.method != 'POST':
        raise Http404
    target = get_object_or_404(Profile.objects.select_related('user'), pk=pk)
    if target.status != 'PEN':
        messages.info(request, 'This account is no longer waiting for approval.')
        return redirect('profile_list')
    if target.role == 'AD' and not request.user.is_superuser:
        raise PermissionDenied('Only a superuser can approve an Admin account.')
    was_login_enabled = target.user.is_active and target.status == 'A'
    with transaction.atomic():
        updated = Profile.objects.filter(pk=target.pk, status='PEN').update(status='A')
        if not updated:
            messages.info(request, 'This account is no longer waiting for approval.')
            return redirect('profile_list')
        target.user.is_active = True
        target.user.save(update_fields=['is_active'])
        StaffAuditLog.objects.create(
            actor=request.user,
            actor_username=request.user.get_username(),
            target_user=target.user,
            target_username=target.user.get_username(),
            action=StaffAuditLog.APPROVED,
            previous_role=target.role,
            new_role=target.role,
            previous_status=target.status,
            new_status='A',
            previous_login_enabled=was_login_enabled,
            new_login_enabled=True,
        )
    messages.success(request, f'{target.user.username} can now sign in as {target.get_role_display()}.')
    return redirect('profile_list')


class ProfileDeleteView(StaffDeleteRequiredMixin, DeleteView):
    """Deletes the staff member's user account (and its profile)."""

    model = Profile
    template_name = 'accounts/staffdelete.html'
    success_url = reverse_lazy('profile_list')

    def get_object(self, queryset=None):
        target = super().get_object(queryset)
        if target.user_id == self.request.user.pk:
            raise PermissionDenied('You cannot delete your own account.')
        if not self.request.user.is_superuser and (
            target.user.is_superuser or target.role == 'AD'
        ):
            raise PermissionDenied('Only a superuser can delete an Admin account.')
        return target

    @transaction.atomic
    def form_valid(self, form):
        target = self.object.user
        username = target.username
        StaffAuditLog.objects.create(
            actor=self.request.user,
            actor_username=self.request.user.get_username(),
            target_user=target,
            target_username=username,
            action=StaffAuditLog.DELETED,
            previous_role=self.object.role,
            previous_status=self.object.status,
            previous_login_enabled=target.is_active and self.object.status == 'A',
        )
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
        from django.db.models import Count, Max, Sum
        from transactions.models import LoyaltyTransaction, Sale

        context = super().get_context_data(**kwargs)
        customer = self.object
        context['ledger'] = customer.loyalty_transactions.select_related('sale', 'created_by')[:50]
        context['recent_sales'] = customer.sale_set.order_by('-date_added')[:10]

        completed = customer.sale_set.filter(status=Sale.STATUS_COMPLETED).aggregate(
            count=Count('pk'), total=Sum('grand_total'), last=Max('date_added'),
        )
        earned = customer.loyalty_transactions.filter(kind=LoyaltyTransaction.EARN).aggregate(n=Sum('points'))['n']
        redeemed = customer.loyalty_transactions.filter(kind=LoyaltyTransaction.REDEEM).aggregate(n=Sum('points'))['n']
        context['summary'] = {
            'sales_count': completed['count'],
            'total_spent': completed['total'] or 0,
            'last_visit': completed['last'],
            'points_earned': earned or 0,
            'points_redeemed': abs(redeemed or 0),
        }
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
