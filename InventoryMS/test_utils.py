"""Small factories shared by the test suites."""
from decimal import Decimal

from django.contrib.auth.models import User

from accounts.models import Customer, Vendor
from store.models import Category, Item

PASSWORD = 'Str0ng-pass-123'


def make_user(username, role='OP', status='A', superuser=False):
    if superuser:
        user = User.objects.create_superuser(username, f'{username}@example.com', PASSWORD)
    else:
        user = User.objects.create_user(username, f'{username}@example.com', PASSWORD)
    profile = user.profile
    profile.role = role if not superuser else 'AD'
    profile.status = status if not superuser else 'A'
    profile.save()
    return user


def make_item(name='Soda', quantity=10, price='50.00', category=None, vendor=None):
    category = category or Category.objects.get_or_create(name='Drinks')[0]
    return Item.objects.create(
        name=name, category=category, quantity=quantity,
        price=Decimal(price), vendor=vendor,
    )


def make_vendor(name='Acme Supplies'):
    return Vendor.objects.create(name=name, phone_number='0712345678')


def make_customer(first_name='Jane', last_name='Doe', points=0):
    return Customer.objects.create(
        first_name=first_name, last_name=last_name, phone='0700000000',
        loyalty_points=points,
    )
