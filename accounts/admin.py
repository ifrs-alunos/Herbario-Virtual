from accounts.models.solicitation import Solicitation
from django.contrib import admin
from .models import Solicitation, Profile

# Register your models here.

admin.site.register(Solicitation)
admin.site.register(Profile)
