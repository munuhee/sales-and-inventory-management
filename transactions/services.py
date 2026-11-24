"""
Sale business logic.

The point of sale page only sends what the cashier chose. Prices, totals,
tax, discount, change and loyalty points are all worked out here from the
database, inside one transaction with the stock rows locked.
"""
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Customer
from store.models import Item

from . import loyalty
from .models import Sale, SaleDetail, LoyaltyTransaction

CENT = Decimal('0.01')
MAX_LINES = 200
MAX_QTY_PER_LINE = 100000


def _money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _decimal(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f'{field} must be a number.')
    if not result.is_finite():
        raise ValidationError(f'{field} must be a number.')
    return result


def _int(value, field):
    try:
        if isinstance(value, float) and not value.is_integer():
            raise ValueError
        return int(str(value))
    except (TypeError, ValueError):
        raise ValidationError(f'{field} must be a whole number.')


def parse_lines(raw_items):
    """Validate and merge cart lines into {item_id: quantity}."""
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError('Add at least one item to the sale.')
    if len(raw_items) > MAX_LINES:
        raise ValidationError('Too many lines in one sale.')
    lines = OrderedDict()
    for raw in raw_items:
        if not isinstance(raw, dict) or 'id' not in raw or 'quantity' not in raw:
            raise ValidationError('Each item needs an id and a quantity.')
        item_id = _int(raw['id'], 'Item id')
        qty = _int(raw['quantity'], 'Quantity')
        if qty < 1 or qty > MAX_QTY_PER_LINE:
            raise ValidationError('Quantities must be at least 1.')
        lines[item_id] = lines.get(item_id, 0) + qty
    return lines


def create_sale(*, user, customer_id, items, tax_percentage=0, amount_paid=0,
                redeem_points=0):
    """
    Create a completed sale. Raises ValidationError with a cashier friendly
    message on any problem; nothing is saved in that case.
    """
    lines = parse_lines(items)
    tax_pct = _decimal(tax_percentage or 0, 'Tax')
    if tax_pct < 0 or tax_pct > 100:
        raise ValidationError('Tax must be between 0 and 100 percent.')
    paid = _decimal(amount_paid or 0, 'Amount paid')
    if paid < 0:
        raise ValidationError('Amount paid cannot be negative.')
    redeem = _int(redeem_points or 0, 'Points to redeem')
    if redeem < 0:
        raise ValidationError('Points to redeem cannot be negative.')

    with transaction.atomic():
        try:
            customer = Customer.objects.select_for_update().get(pk=_int(customer_id, 'Customer'))
        except Customer.DoesNotExist:
            raise ValidationError('Select a valid customer.')

        # Lock every stock row in a stable order to avoid deadlocks.
        locked = {
            item.pk: item
            for item in Item.objects.select_for_update().filter(pk__in=lines.keys()).order_by('pk')
        }
        missing = [pk for pk in lines if pk not in locked]
        if missing:
            raise ValidationError('One or more items no longer exist.')

        sub_total = Decimal('0')
        priced = []
        for item_id, qty in lines.items():
            item = locked[item_id]
            if item.quantity < qty:
                raise ValidationError(
                    f'Not enough stock for {item.name}: {item.quantity} available.'
                )
            line_total = _money(item.price * qty)
            sub_total += line_total
            priced.append((item, qty, item.price, line_total))
        sub_total = _money(sub_total)

        # Loyalty redemption is a discount applied before tax.
        cfg = loyalty.config()
        if redeem:
            if not cfg['enabled']:
                raise ValidationError('Loyalty points are not enabled.')
            if redeem < cfg['min_redeem']:
                raise ValidationError(f'Redeem at least {cfg["min_redeem"]} points.')
            if redeem > customer.loyalty_points:
                raise ValidationError(
                    f'{customer} only has {customer.loyalty_points} points.'
                )
            if redeem > loyalty.max_redeemable(customer.loyalty_points, sub_total):
                raise ValidationError('Points redeemed cannot exceed the bill.')
        discount = loyalty.value_of_points(redeem) if redeem else Decimal('0.00')
        taxable = sub_total - discount
        tax_amount = _money(taxable * tax_pct / Decimal('100'))
        grand_total = _money(taxable + tax_amount)

        if paid < grand_total:
            raise ValidationError(
                f'Amount paid ({_money(paid)}) is less than the total ({grand_total}).'
            )
        change = _money(paid - grand_total)
        earned = loyalty.points_for_amount(taxable)

        sale = Sale.objects.create(
            customer=customer,
            served_by=user if user is not None and user.is_authenticated else None,
            sub_total=sub_total,
            discount_amount=discount,
            tax_percentage=tax_pct,
            tax_amount=tax_amount,
            grand_total=grand_total,
            amount_paid=_money(paid),
            amount_change=change,
            loyalty_points_redeemed=redeem,
            loyalty_points_earned=earned,
        )
        SaleDetail.objects.bulk_create([
            SaleDetail(sale=sale, item=item, price=price, quantity=qty, total_detail=total)
            for item, qty, price, total in priced
        ])
        for item, qty, _, _ in priced:
            Item.adjust_stock(item.pk, -qty)

        if redeem:
            loyalty.apply_points(
                customer.pk, -redeem, LoyaltyTransaction.REDEEM,
                sale=sale, user=user, note=f'Redeemed on {sale.receipt_number}',
            )
        if earned:
            loyalty.apply_points(
                customer.pk, earned, LoyaltyTransaction.EARN,
                sale=sale, user=user, note=f'Earned on {sale.receipt_number}',
            )
    return sale


def void_sale(sale, *, user, reason=''):
    """
    Void a completed sale: restore stock, give back redeemed points and take
    back earned points. The sale row is kept for the audit trail.
    """
    with transaction.atomic():
        sale = Sale.objects.select_for_update().get(pk=sale.pk)
        if sale.is_voided:
            raise ValidationError('This sale has already been voided.')

        for detail in sale.saledetail_set.select_related('item').order_by('item_id'):
            Item.adjust_stock(detail.item_id, detail.quantity)

        customer = Customer.objects.select_for_update().get(pk=sale.customer_id)
        net_points = sale.loyalty_points_redeemed - sale.loyalty_points_earned
        if net_points < 0 and customer.loyalty_points < -net_points:
            # Customer already spent the points earned on this sale; take what
            # is left rather than blocking the void.
            net_points = -customer.loyalty_points
        if net_points:
            loyalty.apply_points(
                customer.pk, net_points, LoyaltyTransaction.REVERSAL,
                sale=sale, user=user, note=f'Void of {sale.receipt_number}',
            )

        sale.status = Sale.STATUS_VOIDED
        sale.voided_at = timezone.now()
        sale.voided_by = user if user is not None and user.is_authenticated else None
        sale.void_reason = (reason or '')[:200]
        sale.save(update_fields=['status', 'voided_at', 'voided_by', 'void_reason'])
    return sale
