from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField


STATUS_CHOICES = [
    ('INA', 'Inactive'),
    ('A', 'Active'),
    ('OL', 'On_leave')
]

ROLE_CHOICES = [
    ('OP', 'Operative'),
    ('EX', 'Executive'),
    ('AD', 'Admin')
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    slug = AutoSlugField(unique=True, verbose_name=('Account ID'), populate_from='email')
    profile_picture = ProcessedImageField(default='profile_pics/default.jpg', upload_to='profile_pics', format='JPEG',
                                processors = [ResizeToFill(150,150)],
                                options={ 'quality': 100})
    telephone = PhoneNumberField(null=True,blank=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=12, blank=False, null=False, default='INA')
    role = models.CharField(choices=ROLE_CHOICES, max_length=12, blank=True, null=True)

    @property
    def imageURL(self):
        try:
            url= self.image.url
        except:
            url = ''
        return url

    def __str__(self):
        return f'{self.user.username} Profile'

    class Meta:
        ordering = ["slug"]

class Vendor(models.Model):
    name = models.CharField(max_length=50)
    slug = AutoSlugField(unique=True , populate_from='name')
    phone_number = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name