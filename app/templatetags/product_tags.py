"""
app/templatetags/product_tags.py

Register this file in your Django app's templatetags/ folder.
Make sure the folder has an __init__.py file.

Usage in template:
    {% load product_tags %}
    {{ v.attributes|to_json }}
    {{ v.attributes|jsonify_keys }}
"""

import json
from django import template

register = template.Library()


@register.filter(name="to_json")
def to_json(value):
    """Serialize a Python dict/list/value to a JSON string (safe for use in HTML attributes)."""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return "{}"


@register.filter(name="jsonify_keys")
def jsonify_keys(attrs):
    """
    Build a pipe-separated key:val string for the data-vkey attribute on variant cards.
    Skips meta-keys like sale_price, points, description.

    Example:
        {'Color': 'Red', 'Size': 'M', 'sale_price': '100'}
        → 'Color:Red|Size:M'
    """
    META_KEYS = {"sale_price", "points", "description"}
    if not isinstance(attrs, dict):
        return ""
    return "|".join(
        f"{k}:{v}"
        for k, v in attrs.items()
        if k not in META_KEYS
    )
