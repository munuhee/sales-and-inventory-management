"""
Fill an empty database with realistic demo data.

    python manage.py seed_demo

Creates three sign-ins (password "demo-pass-123"):
    admin    Admin      everything, including staff
    manager  Executive  stock, purchasing, finance, voids
    cashier  Operative  point of sale

Refuses to run when DEBUG is off unless --force is given.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Customer, Vendor
from bills.models import Bill
from invoice.models import Invoice
from store.models import Category, Delivery, Item
from transactions.models import LoyaltyTransaction, Purchase, Sale
from transactions.services import create_sale, void_sale

PASSWORD = 'demo-pass-123'

CATALOGUE = {
    'Electronics': [
        ('Samsung 43in Smart TV', '38500.00'), ('HDMI cable 2m', '650.00'),
        ('Wall bracket 32-55in', '2400.00'), ('Bluetooth speaker', '4200.00'),
        ('Power bank 20000mAh', '3100.00'),
    ],
    'Groceries': [
        ('Maize flour 2kg', '210.00'), ('Basmati rice 5kg', '1150.00'),
        ('Cooking oil 3L', '980.00'), ('Sugar 2kg', '320.00'), ('Tea leaves 500g', '290.00'),
    ],
    'Beverages': [
        ('Mineral water 1.5L', '90.00'), ('Orange juice 1L', '260.00'),
        ('Ground coffee 250g', '650.00'), ('Soda 500ml', '80.00'),
    ],
    'Household': [
        ('Laundry detergent 2kg', '720.00'), ('Dish soap 750ml', '240.00'),
        ('Toilet paper 10 pack', '560.00'), ('Bleach 1L', '180.00'),
    ],
    'Stationery': [
        ('A4 paper ream', '650.00'), ('Ballpoint pens 10 pack', '150.00'),
        ('Exercise books 5 pack', '320.00'),
    ],
}

VENDORS = [
    ('Mombasa Wholesalers', '0711 222 333', 'Moi Avenue'),
    ('Nairobi Electronics Hub', '0722 444 555', 'Luthuli Avenue'),
    ('Coast Beverages Ltd', '0733 666 777', 'Nyali'),
    ('Kilimo Fresh Supplies', '0700 888 999', 'Kongowea'),
]

CUSTOMERS = [
    ('Walk-in', 'Customer', ''), ('Peter', 'Otieno', '0712 345 678'),
    ('Amina', 'Hassan', '0723 456 789'), ('Grace', 'Wambui', '0734 567 890'),
    ('Brian', 'Kiptoo', '0745 678 901'), ('Fatuma', 'Ali', '0756 789 012'),
    ('David', 'Mwangi', '0767 890 123'), ('Mercy', 'Achieng', '0778 901 234'),
]


class Command(BaseCommand):
    help = 'Load realistic demo data (only on an empty database).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Allow running with DEBUG off.')

    def handle(self, *args, force=False, **options):
        if not settings.DEBUG and not force:
            raise CommandError('Refusing to seed demo data with DEBUG off. Use --force if you really mean it.')
        if Item.objects.exists() or Sale.objects.exists():
            raise CommandError('The database already has data. Seed only an empty database.')

        rng = random.Random(42)
        with transaction.atomic():
            self._user('admin', 'Stephen', 'Murichu', 'AD', superuser=True)
            manager = self._user('manager', 'Joyce', 'Njeri', 'EX')
            cashier = self._user('cashier', 'Mary', 'Wanjiku', 'OP')
            pending = self._user('kevin', 'Kevin', 'Omondi', 'OP')
            pending.profile.status = 'PEN'
            pending.profile.save()

            vendors = [Vendor.objects.create(name=n, phone_number=p, address=a) for n, p, a in VENDORS]
            by_name = {vendor.name: vendor for vendor in vendors}
            supplier = {
                'Electronics': by_name['Nairobi Electronics Hub'],
                'Groceries': by_name['Kilimo Fresh Supplies'],
                'Beverages': by_name['Coast Beverages Ltd'],
                'Household': by_name['Mombasa Wholesalers'],
                'Stationery': by_name['Mombasa Wholesalers'],
            }
            items = []
            for category_name, products in CATALOGUE.items():
                category = Category.objects.create(name=category_name)
                vendor = supplier[category_name]
                for name, price in products:
                    items.append(Item.objects.create(
                        name=name, category=category, price=Decimal(price),
                        quantity=0, vendor=vendor,
                        description=f'{name} supplied by {vendor.name}.',
                    ))

            # Stock arrives through received purchase orders.
            for item in items:
                Purchase.objects.create(
                    item=item, vendor=item.vendor, quantity=rng.randint(20, 60),
                    price=(item.price * Decimal('0.72')).quantize(Decimal('0.01')),
                    delivery_status='S', delivery_date=timezone.now() - timedelta(days=32),
                    description='Opening stock',
                )
            for item in rng.sample(items, 4):
                Purchase.objects.create(
                    item=item, vendor=item.vendor, quantity=rng.randint(10, 30),
                    price=(item.price * Decimal('0.70')).quantize(Decimal('0.01')),
                    delivery_status='P', delivery_date=timezone.now() + timedelta(days=rng.randint(2, 9)),
                    description='Restock order',
                )

            customers = [Customer.objects.create(first_name=f, last_name=l, phone=p or None) for f, l, p in CUSTOMERS]

            # About a month of sales.
            sales = []
            for days_ago in range(29, -1, -1):
                # Times increase through the day, in the order the sales are
                # made, so receipts and the loyalty ledger stay chronological.
                count = rng.randint(2, 6)
                opening = timezone.now() - timedelta(days=days_ago, hours=10)
                times = sorted(opening + timedelta(minutes=rng.randint(0, 9 * 60)) for _ in range(count))
                for when in times:
                    picks = rng.sample(items, rng.randint(1, 4))
                    lines = []
                    for item in picks:
                        item.refresh_from_db()
                        if item.quantity > 2:
                            lines.append({'id': item.pk, 'quantity': rng.randint(1, 2)})
                    if not lines:
                        continue
                    customer = rng.choice(customers)
                    customer.refresh_from_db()
                    redeem = customer.loyalty_points if customer.loyalty_points >= 50 and rng.random() < 0.3 else 0
                    try:
                        sale = create_sale(
                            user=rng.choice([cashier, cashier, manager]), customer_id=customer.pk,
                            items=lines, tax_percentage='16', amount_paid='1000000',
                            redeem_points=redeem,
                        )
                    except Exception:
                        continue
                    # Realistic cash: round up to the next 50 or 100.
                    step = Decimal('100') if sale.grand_total > 1000 else Decimal('50')
                    paid = ((sale.grand_total / step).to_integral_value(rounding='ROUND_CEILING')) * step
                    Sale.objects.filter(pk=sale.pk).update(
                        date_added=when, amount_paid=paid, amount_change=paid - sale.grand_total,
                    )
                    LoyaltyTransaction.objects.filter(sale=sale).update(created_at=when)
                    sales.append(sale)

            if sales:
                void_sale(sales[len(sales) // 2], user=manager, reason='Customer returned all items')

            # A few low stock items for the dashboard.
            for item in items[:3]:
                Item.objects.filter(pk=item.pk).update(quantity=rng.randint(0, 4))

            now = timezone.now()
            for offset, (item, name, place, done) in enumerate([
                (items[0], 'Peter Otieno', 'Nyali', True),
                (items[5], 'Amina Hassan', 'Bamburi', False),
                (items[1], 'Grace Wambui', 'Likoni', False),
            ]):
                Delivery.objects.create(item=item, customer_name=name, phone_number='+254712345678',
                                        location=place, date=now + timedelta(days=offset - 1), is_delivered=done)

            Invoice.objects.create(customer_name='Kilimo Traders Ltd', contact_number='0722 000 111',
                                   item=items[0], price_per_item=Decimal('37000'), quantity=Decimal('3'),
                                   shipping=Decimal('1500'))
            Invoice.objects.create(customer_name='Bahari Hotel', contact_number='0733 222 444',
                                   item=items[6], price_per_item=Decimal('1100'), quantity=Decimal('20'),
                                   shipping=Decimal('800'))

            Bill.objects.create(institution_name='Kenya Power', payment_details='Paybill 888880',
                                description='November electricity', amount=Decimal('18450'), status=False)
            Bill.objects.create(institution_name='Mombasa Water', payment_details='Paybill 500700',
                                description='November water', amount=Decimal('3200'), status=True)
            Bill.objects.create(institution_name='Shop landlord', payment_details='Bank transfer',
                                description='December rent', amount=Decimal('65000'), status=False)

        self.stdout.write(self.style.SUCCESS(
            f'Demo data loaded: {len(items)} products, {len(sales)} sales. '
            f'Sign in as admin, manager or cashier with password "{PASSWORD}".'
        ))

    def _user(self, username, first, last, role, superuser=False):
        if superuser:
            user = User.objects.create_superuser(username, f'{username}@example.com', PASSWORD,
                                                 first_name=first, last_name=last)
        else:
            user = User.objects.create_user(username, f'{username}@example.com', PASSWORD,
                                            first_name=first, last_name=last)
        profile = user.profile
        profile.first_name, profile.last_name = first, last
        profile.role = 'AD' if superuser else role
        profile.status = 'A'
        profile.save()
        return user
