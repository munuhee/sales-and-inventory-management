from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from django_extensions.db.fields import AutoSlugField
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from phonenumber_field.modelfields import PhoneNumberField


# Profile status and roles. Only Active profiles may sign in.
STATUS_CHOICES = [
    ('PEN', 'Pending approval'),
    ('A', 'Active'),
    ('INA', 'Inactive'),
    ('OL', 'On leave')
]

ROLE_CHOICES = [
    ('OP', 'Operative'),
    ('EX', 'Executive'),
    ('AD', 'Admin')
]


class Profile(models.Model):
    """
    Staff profile attached to every user account.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name='User'
    )
    slug = AutoSlugField(
        unique=True,
        verbose_name='Account ID',
        populate_from='email'
    )

    profile_picture = ProcessedImageField(
        default='profile_pics/default.jpg',
        upload_to='profile_pics',
        format='JPEG',
        processors=[ResizeToFill(150, 150)],
        options={'quality': 90}
    )
    telephone = PhoneNumberField(
        null=True, blank=True, verbose_name='Telephone'
    )
    email = models.EmailField(
        max_length=150, blank=True, null=True, unique=True,
        verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=30, blank=True, verbose_name='First Name'
    )
    last_name = models.CharField(
        max_length=30, blank=True, verbose_name='Last Name'
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=12,
        default='INA',
        verbose_name='Status'
    )
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=12,
        default='OP',
        verbose_name='Role'
    )

    @property
    def image_url(self):
        """
        Returns the URL of the profile picture, or an empty string.
        """
        try:
            return self.profile_picture.url
        except (AttributeError, ValueError):
            return ''

    @property
    def has_picture(self):
        """True only for an uploaded picture that exists on disk."""
        name = getattr(self.profile_picture, 'name', '') or ''
        if not name or name == 'profile_pics/default.jpg':
            return False
        try:
            return self.profile_picture.storage.exists(name)
        except Exception:
            return False

    @property
    def initials(self):
        parts = [p for p in self.display_name.replace('.', ' ').split() if p]
        return ''.join(p[0] for p in parts[:2]).upper() or '?'

    @property
    def display_name(self):
        full = f'{self.first_name} {self.last_name}'.strip()
        return full or self.user.get_full_name() or self.user.username

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        ordering = ['slug']
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'


class StaffAuditLog(models.Model):
    """Immutable record of staff account and access-control changes."""

    CREATED = 'CREATED'
    UPDATED = 'UPDATED'
    APPROVED = 'APPROVED'
    DELETED = 'DELETED'
    ACTION_CHOICES = [
        (CREATED, 'Account created'),
        (UPDATED, 'Access updated'),
        (APPROVED, 'Account approved'),
        (DELETED, 'Account deleted'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='staff_audit_actions',
    )
    actor_username = models.CharField(max_length=150)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='staff_audit_events',
    )
    target_username = models.CharField(max_length=150)
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    previous_role = models.CharField(max_length=12, blank=True, choices=ROLE_CHOICES)
    new_role = models.CharField(max_length=12, blank=True, choices=ROLE_CHOICES)
    previous_status = models.CharField(max_length=12, blank=True, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=12, blank=True, choices=STATUS_CHOICES)
    previous_login_enabled = models.BooleanField(null=True, blank=True)
    new_login_enabled = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'Staff audit event'
        verbose_name_plural = 'Staff audit events'


class Vendor(models.Model):
    """
    Represents a vendor with contact and address information.
    """
    name = models.CharField(max_length=50, verbose_name='Name')
    slug = AutoSlugField(
        unique=True,
        populate_from='name',
        verbose_name='Slug'
    )
    # Text, not a number: phone numbers keep leading zeros and "+".
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Phone Number'
    )
    address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Address'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'


class Customer(models.Model):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    address = models.TextField(max_length=256, blank=True, null=True)
    email = models.EmailField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    # Balance only. Changed through transactions.loyalty, never edited by hand,
    # so every change has a matching LoyaltyTransaction ledger row.
    loyalty_points = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        db_table = 'Customers'
        ordering = ['first_name', 'last_name']

    def __str__(self) -> str:
        return self.get_full_name()

    def get_full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    @property
    def loyalty_value(self):
        """Money value of the current points balance."""
        from decimal import Decimal
        return Decimal(self.loyalty_points) * Decimal(
            str(settings.LOYALTY['point_value'])
        )

    def to_select2(self):
        return {
            "id": self.id,
            "text": self.get_full_name(),
            "label": self.get_full_name(),
            "value": self.id,
            "phone": self.phone or '',
            "loyalty_points": self.loyalty_points,
        }
