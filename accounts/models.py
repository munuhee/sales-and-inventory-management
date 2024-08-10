from django.db import models
from django.contrib.auth.models import User

from django_extensions.db.fields import AutoSlugField
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from phonenumber_field.modelfields import PhoneNumberField


# Define choices for profile status and roles
STATUS_CHOICES = [
    ('INA', 'Inactive'),
    ('A', 'Active'),
    ('OL', 'On leave')
]

ROLE_CHOICES = [
    ('OP', 'Operative'),
    ('EX', 'Executive'),
    ('AD', 'Admin')
]


class Profile(models.Model):
    """
    Represents a user profile containing personal and account-related details.
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
        options={'quality': 100}
    )
    telephone = PhoneNumberField(
        null=True, blank=True, verbose_name='Telephone'
    )
    email = models.EmailField(
        max_length=150, blank=True, null=True, verbose_name='Email'
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
        blank=True,
        null=True,
        verbose_name='Role'
    )

    @property
    def image_url(self):
        """
        Returns the URL of the profile picture.
        Returns an empty string if the image is not available.
        """
        try:
            return self.profile_picture.url
        except AttributeError:
            return ''

    def __str__(self):
        """
        Returns a string representation of the profile.
        """
        return f"{self.user.username} Profile"

    class Meta:
        """Meta options for the Profile model."""
        ordering = ['slug']
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'


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
    phone_number = models.BigIntegerField(
        blank=True, null=True, verbose_name='Phone Number'
    )
    address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Address'
    )

    def __str__(self):
        """
        Returns a string representation of the vendor.
        """
        return self.name

    class Meta:
        """Meta options for the Vendor model."""
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'


class Customer(models.Model):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    address = models.TextField(max_length=256, blank=True, null=True)
    email = models.EmailField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    loyalty_points = models.IntegerField(default=0)

    class Meta:
        db_table = 'Customers'

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def to_select2(self):
        item = {
            "label": self.get_full_name(),
            "value": self.id
        }
        return item
