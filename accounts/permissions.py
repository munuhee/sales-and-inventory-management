"""
Role based access control.

Roles (lowest to highest):
    Operative  (OP)  point of sale: sell, view stock, customers, deliveries
    Executive  (EX)  manager: products, purchases, vendors, invoices, bills,
                     exports, voiding sales and deleting business records
    Admin      (AD)  everything, including staff accounts and roles

Django superusers are always treated as Admin. Users whose profile is not
Active cannot use the app at all (see ActiveProfileMiddleware).
"""
from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

OPERATIVE = 'OP'
EXECUTIVE = 'EX'
ADMIN = 'AD'

ROLE_LEVELS = {OPERATIVE: 1, EXECUTIVE: 2, ADMIN: 3}

OPERATIVE_CAPABILITIES = frozenset({
    'dashboard.view', 'sales.view', 'sales.create', 'customers.view',
    'customers.create', 'customers.update', 'deliveries.view',
    'deliveries.create', 'deliveries.update', 'inventory.view',
    'categories.view', 'invoices.view', 'profile.self.view',
    'profile.self.update',
})
EXECUTIVE_CAPABILITIES = OPERATIVE_CAPABILITIES | frozenset({
    'inventory.manage', 'categories.manage', 'purchases.manage',
    'vendors.manage', 'finance.manage', 'sales.void', 'exports.run',
    'customers.delete', 'customers.loyalty.adjust', 'invoices.manage',
})
ADMIN_CAPABILITIES = EXECUTIVE_CAPABILITIES | frozenset({
    'staff.view', 'staff.create', 'staff.update', 'staff.delete',
    'staff.approve',
})
ROLE_CAPABILITIES = {
    OPERATIVE: OPERATIVE_CAPABILITIES,
    EXECUTIVE: EXECUTIVE_CAPABILITIES,
    ADMIN: ADMIN_CAPABILITIES,
}


def get_profile(user):
    try:
        return user.profile
    except ObjectDoesNotExist:
        return None


def is_active_member(user):
    """Authenticated and allowed to use the app."""
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    profile = get_profile(user)
    return profile is not None and profile.status == 'A'


def role_level(user):
    if not is_active_member(user):
        return 0
    if user.is_superuser:
        return ROLE_LEVELS[ADMIN]
    profile = get_profile(user)
    # Active staff without an explicit role get the lowest role.
    return ROLE_LEVELS.get(profile.role or OPERATIVE, ROLE_LEVELS[OPERATIVE])


def has_role(user, min_role):
    minimum = ROLE_LEVELS.get(min_role)
    return minimum is not None and role_level(user) >= minimum


def has_capability(user, capability):
    """Check an explicit application capability; unknown capabilities fail closed."""
    if not is_active_member(user):
        return False
    if user.is_superuser:
        return True
    profile = get_profile(user)
    role = profile.role if profile and profile.role in ROLE_CAPABILITIES else OPERATIVE
    return capability in ROLE_CAPABILITIES[role]


def is_manager(user):
    return has_role(user, EXECUTIVE)


def is_admin(user):
    return has_role(user, ADMIN)


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Class based view guard. Set ``min_role`` on the view."""

    min_role = OPERATIVE

    def test_func(self):
        return has_role(self.request.user, self.min_role)


class ManagerRequiredMixin(RoleRequiredMixin):
    min_role = EXECUTIVE


class AdminRequiredMixin(RoleRequiredMixin):
    min_role = ADMIN


def role_required(min_role=OPERATIVE):
    """Function view guard: login first, then 403 if the role is too low."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_role(request.user, min_role):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def capability_required(capability):
    """Function view guard for an explicit application capability."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_capability(request.user, capability):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class CapabilityRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_capability = ''

    def test_func(self):
        return has_capability(self.request.user, self.required_capability)


class StaffViewRequiredMixin(CapabilityRequiredMixin):
    required_capability = 'staff.view'


class StaffCreateRequiredMixin(CapabilityRequiredMixin):
    required_capability = 'staff.create'


class StaffUpdateRequiredMixin(CapabilityRequiredMixin):
    required_capability = 'staff.update'


class StaffDeleteRequiredMixin(CapabilityRequiredMixin):
    required_capability = 'staff.delete'
