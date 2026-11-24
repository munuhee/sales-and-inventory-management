from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(value, with_currency=True):
    """1234.5 -> 'Ksh 1,234.50'. Use money:False for the number only."""
    if value is None or value == '':
        return ''
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return value
    text = f'{amount:,.2f}'
    if with_currency is False or with_currency == 'False':
        return text
    return f"{settings.BUSINESS.get('currency', 'Ksh')} {text}"


@register.filter
def qty(value):
    """Drop a trailing .00 from quantities: 3.00 -> 3, 2.50 -> 2.5."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value
    if number == number.to_integral():
        return f'{int(number):,}'
    return f'{number.normalize():f}'


@register.filter
def percent(value):
    try:
        number = Decimal(str(value)).normalize()
    except (InvalidOperation, ValueError):
        return value
    return f'{number:f}%'
