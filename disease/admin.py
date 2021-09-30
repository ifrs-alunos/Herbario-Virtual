from django.contrib import admin
from .models import *

# Register your models here.

class PhotoInline(admin.TabularInline):
    model = PhotoDisease

class DiseaseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name_disease',)}
    list_display = ('name_disease', 'scientific_name_disease','culture_disease',)
    list_filter = ('culture_disease',)
    search_fields = ('name_disease', 'scientific_name_disease', 'symptoms_disease')
    inlines = [PhotoInline, ]

admin.site.register(Region)
admin.site.register(State)
admin.site.register(Disease, DiseaseAdmin)
admin.site.register(Culture)
admin.site.register(ConditionSolicitation)
admin.site.register(Condition)