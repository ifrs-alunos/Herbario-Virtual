from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def is_admin(user: User):
    print(user.groups)
    return user.is_staff or user.groups.filter(name='admins').exists()
