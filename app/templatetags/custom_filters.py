from django import template
import json

register = template.Library()

@register.filter
def jsonify_keys(value):
    """
    Dict keys ko sorted JSON string bana deta hai (stable variant key)
    """
    if not isinstance(value, dict):
        return ""

    sorted_dict = dict(sorted(value.items()))
    return json.dumps(sorted_dict, sort_keys=True)
