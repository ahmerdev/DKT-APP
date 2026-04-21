# app/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def dictmax(d):
    """Return the max value of a dict"""
    if not d:
        return 0
    return max(d.values())


@register.filter
def div(value, arg):
    return value / arg

@register.filter
def mul(value, arg):
    return value * arg


