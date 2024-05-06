from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def format_phone_number(phone_number: str):
    return f"+{phone_number[:2]} ({phone_number[2:4]}) {phone_number[4:8]}-{phone_number[8:]}"

