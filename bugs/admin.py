from django.contrib import admin

from .models import *
# Register your models here.

class PhotoInline(admin.TabularInline):
    model = Photo


class PlantAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'scientific_name', 'family',)
    list_filter = ('family',)
    search_fields = ('name', 'scientific_name', 'description')
    inlines = [PhotoInline, ]


admin.site.register(Plant, PlantAdmin)
admin.site.register(Family)
admin.site.register(State)
admin.site.register(Region)
# admin.site.register(Division)
