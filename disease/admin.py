from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Region)
admin.site.register(State)
admin.site.register(Disease)
admin.site.register(Culture)
admin.site.register(Conditions)