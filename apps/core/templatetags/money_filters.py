from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def format_money(value):
    try:
        val = Decimal(str(value))
    except Exception:
        return str(value)
    sign = ''
    if val < 0:
        sign = '-'
        val = abs(val)
    parts = f'{val:.2f}'.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    chunks = []
    while len(integer_part) > 3:
        chunks.append(integer_part[-3:])
        integer_part = integer_part[:-3]
    chunks.append(integer_part)
    formatted = sign + ' '.join(reversed(chunks))
    return f'{formatted},{decimal_part}'
