"""
Loyalty points: earning, redeeming, reversing and manual adjustments.

Every balance change goes through ``apply_points`` which locks the customer
row, refuses to go negative and writes a LoyaltyTransaction ledger row.
"""
from decimal import Decimal, ROUND_FLOOR

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Customer


def config():
    cfg = settings.LOYALTY
    return {
        'enabled': cfg.get('enabled', True),
        'earn_per': Decimal(str(cfg.get('earn_per', '100'))),
        'point_value': Decimal(str(cfg.get('point_value', '1.00'))),
        'min_redeem': int(cfg.get('min_redeem', 0)),
    }


def points_for_amount(amount):
    """Points earned for a spend amount (after discounts, before tax)."""
    cfg = config()
    if not cfg['enabled'] or cfg['earn_per'] <= 0 or amount <= 0:
        return 0
    return int((Decimal(amount) / cfg['earn_per']).to_integral_value(rounding=ROUND_FLOOR))


def value_of_points(points):
    return (Decimal(points) * config()['point_value']).quantize(Decimal('0.01'))


def max_redeemable(balance, sub_total):
    """Most points usable on a sale: limited by balance and by the bill."""
    cfg = config()
    if not cfg['enabled'] or cfg['point_value'] <= 0:
        return 0
    by_bill = int((Decimal(sub_total) / cfg['point_value']).to_integral_value(rounding=ROUND_FLOOR))
    return max(0, min(balance, by_bill))


def apply_points(customer_id, points, kind, *, sale=None, user=None, note=''):
    """Change a customer's balance by ``points`` and record it in the ledger."""
    from .models import LoyaltyTransaction

    points = int(points)
    if points == 0:
        return None
    with transaction.atomic():
        customer = Customer.objects.select_for_update().get(pk=customer_id)
        new_balance = customer.loyalty_points + points
        if new_balance < 0:
            raise ValidationError(
                f'{customer} has {customer.loyalty_points} points; '
                f'cannot remove {-points}.'
            )
        customer.loyalty_points = new_balance
        customer.save(update_fields=['loyalty_points'])
        return LoyaltyTransaction.objects.create(
            customer=customer,
            sale=sale,
            kind=kind,
            points=points,
            balance_after=new_balance,
            note=note[:200],
            created_by=user if user is not None and user.is_authenticated else None,
        )
