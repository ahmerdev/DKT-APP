from django import template
register = template.Library()

@register.filter
def filter_status(orders, status):
    return [o for o in orders if o.status == status]
