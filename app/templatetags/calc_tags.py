from django import template

register = template.Library()

@register.filter
def percent(value, max_value):
    try:
        value = float(value)
        max_value = float(max_value)
        if max_value == 0:
            return 0
        return (value / max_value) * 100
    except:
        return 0
