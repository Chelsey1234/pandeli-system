from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def peso(value):
    """Format value as Philippine Peso"""
    try:
        # Convert to float or Decimal and format with 2 decimal places
        amount = float(value)
        return f"₱{amount:,.2f}"
    except (ValueError, TypeError):
        return "₱0.00"

@register.filter
def multiply(value, arg):
    """Multiply value by arg. Use: {{ value|multiply:arg }}"""
    try:
        return float(value or 0) * float(arg or 0)
    except (ValueError, TypeError):
        return 0


@register.filter
def peso_no_decimal(value):
    """Format value as Philippine Peso without decimals"""
    try:
        amount = float(value)
        return f"₱{amount:,.0f}"
    except (ValueError, TypeError):
        return "₱0"