from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.cache import cache

from .models import Profile, Customer, Vendor, STATUS_CHOICES, ROLE_CHOICES


def _client_ip(request):
    if request is None:
        return 'unknown'
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


class LoginForm(AuthenticationForm):
    """
    Login with brute force throttling and staff approval checks.

    After LOGIN_MAX_ATTEMPTS failures for the same username and IP the pair is
    locked for LOGIN_LOCKOUT_SECONDS.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        'inactive': 'Sign-in access is disabled. Contact an administrator.',
        'locked': 'Too many failed attempts. Try again in a few minutes.',
        'pending': 'Your account is awaiting approval by an administrator.',
        'inactive_profile': 'Your account is not active. Contact an administrator.',
    }

    def _throttle_key(self):
        username = (self.data.get('username') or '').strip().lower()
        return f'login-fail:{username}:{_client_ip(self.request)}'

    def clean(self):
        key = self._throttle_key()
        if cache.get(key, 0) >= settings.LOGIN_MAX_ATTEMPTS:
            raise forms.ValidationError(self.error_messages['locked'], code='locked')
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, settings.LOGIN_LOCKOUT_SECONDS)
            raise
        cache.delete(key)
        return cleaned

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_superuser:
            return
        profile = getattr(user, 'profile', None)
        if profile is None or profile.status == 'PEN':
            raise forms.ValidationError(self.error_messages['pending'], code='pending')
        if profile.status != 'A':
            raise forms.ValidationError(
                self.error_messages['inactive_profile'], code='inactive_profile'
            )


class CreateUserForm(UserCreationForm):
    """Self sign-up. The account stays pending until an admin approves it."""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class UserUpdateForm(forms.ModelForm):
    """Lets a user change their account username."""

    class Meta:
        model = User
        fields = ['username']


class ProfileUpdateForm(forms.ModelForm):
    """Self service profile edit. Role and status are not editable here."""

    class Meta:
        model = Profile
        fields = ['telephone', 'email', 'first_name', 'last_name', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.instance.email:
            self.initial['email'] = self.instance.user.email

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture and hasattr(picture, 'size') and picture.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Profile pictures must be 2 MB or smaller.')
        return picture

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        user_id = self.instance.user_id
        if email and User.objects.filter(email__iexact=email).exclude(pk=user_id).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class StaffCreateForm(UserCreationForm):
    """Admin creates a staff account with a role, active straight away."""
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='OP')
    status = forms.ChoiceField(choices=STATUS_CHOICES, initial='A')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            choice for choice in ROLE_CHOICES
            if acting_user and acting_user.is_superuser or choice[0] != 'AD'
        ]
        self.fields['role'].help_text = (
            'Operative: sales and daily operations. Executive: inventory and finance. '
            'Admin: staff access and all application areas.'
        )
        self.fields['status'].choices = [
            choice for choice in STATUS_CHOICES if choice[0] != 'PEN'
        ]
        self.fields['status'].help_text = 'Only active staff can sign in.'

    def clean_role(self):
        role = self.cleaned_data['role']
        if role == 'AD' and not (self.acting_user and self.acting_user.is_superuser):
            raise forms.ValidationError('Only a superuser can grant the Admin role.')
        return role

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.status = self.cleaned_data['status']
            profile.first_name = self.cleaned_data.get('first_name', '')
            profile.last_name = self.cleaned_data.get('last_name', '')
            email = self.cleaned_data.get('email')
            if email and not Profile.objects.filter(email=email).exclude(pk=profile.pk).exists():
                profile.email = email
            profile.save()
            user.is_active = profile.status == 'A'
            user.save(update_fields=['is_active'])
        return user


class StaffUpdateForm(forms.ModelForm):
    """Admin edits a staff member's role, status and details."""

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'telephone', 'email', 'role', 'status']

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        if acting_user and not acting_user.is_superuser:
            self.fields['role'].choices = [
                choice for choice in ROLE_CHOICES
                if choice[0] != 'AD' or self.instance.role == 'AD'
            ]
        self.fields['status'].choices = [
            choice for choice in STATUS_CHOICES if choice[0] != 'PEN'
        ]
        if self.instance.status == 'PEN':
            self.fields['status'].choices = list(STATUS_CHOICES[:1]) + self.fields['status'].choices
        self.fields['role'].help_text = (
            'Operative: sales and daily operations. Executive: inventory and finance. '
            'Admin: staff access and all application areas.'
        )
        self.fields['status'].help_text = 'Inactive and On leave accounts are signed out immediately.'
        self.fields['login_enabled'] = forms.BooleanField(
            required=False,
            label='Login enabled',
            help_text='Allow this person to sign in. This is separate from their employment status.',
            initial=self.instance.user.is_active and self.instance.status == 'A',
        )

    def clean(self):
        cleaned = super().clean()
        target = self.instance.user
        acting = self.acting_user
        if acting is not None and target.pk == acting.pk and not acting.is_superuser:
            if (
                cleaned.get('status') != 'A'
                or cleaned.get('role') != 'AD'
                or not cleaned.get('login_enabled')
            ):
                raise forms.ValidationError(
                    'You cannot remove your own admin role or deactivate yourself.'
                )
        if target.is_superuser and not (acting and acting.is_superuser):
            raise forms.ValidationError('Only a superuser can change a superuser account.')
        if acting and not acting.is_superuser:
            if target.role == 'AD':
                raise forms.ValidationError('Only a superuser can modify an Admin account.')
            if cleaned.get('role') == 'AD':
                raise forms.ValidationError('Only a superuser can grant the Admin role.')
        if target.is_superuser and (
            cleaned.get('role') != 'AD' or cleaned.get('status') != 'A'
            or not cleaned.get('login_enabled')
        ):
            raise forms.ValidationError('A superuser account must retain Admin and Active access.')
        if cleaned.get('status') != 'A':
            cleaned['login_enabled'] = False
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            profile.user.is_active = bool(self.cleaned_data.get('login_enabled'))
            profile.user.save(update_fields=['is_active'])
        return profile


class CustomerForm(forms.ModelForm):
    """Create or update a customer. Loyalty points are earned, not typed."""

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'address', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'rows': 3
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
        }


class LoyaltyAdjustmentForm(forms.Form):
    """Manager correction of a customer's points, recorded in the ledger."""
    points = forms.IntegerField(
        help_text='Positive to add points, negative to remove them.',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    note = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason'}),
    )

    def clean_points(self):
        points = self.cleaned_data['points']
        if points == 0:
            raise forms.ValidationError('Enter a non-zero number of points.')
        return points


class VendorForm(forms.ModelForm):
    """Form for creating/updating vendor information."""

    class Meta:
        model = Vendor
        fields = ['name', 'phone_number', 'address']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Vendor Name'}
            ),
            'phone_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Phone Number'}
            ),
            'address': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Address'}
            ),
        }
