from django.db import migrations
from django.db.models import F


def backfill(apps, schema_editor):
    Purchase = apps.get_model('transactions', 'Purchase')
    Customer = apps.get_model('accounts', 'Customer')
    LoyaltyTransaction = apps.get_model('transactions', 'LoyaltyTransaction')

    # The old code added each purchase's quantity to stock when it was
    # created. Record that, so later edits adjust by the difference instead
    # of adding the full quantity again.
    Purchase.objects.update(stock_applied=F('quantity'))

    # Open the loyalty ledger with each customer's existing balance so the
    # ledger always sums to the balance.
    LoyaltyTransaction.objects.bulk_create([
        LoyaltyTransaction(
            customer_id=customer.pk,
            kind='ADJUST',
            points=customer.loyalty_points,
            balance_after=customer.loyalty_points,
            note='Opening balance',
        )
        for customer in Customer.objects.filter(loyalty_points__gt=0)
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_hardening'),
        ('accounts', '0002_hardening'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
