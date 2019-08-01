from django.contrib import admin

from .models import Plant
# Register your models here.

class PlantAdmin(admin.ModelAdmin):

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'scientific_name', 'order', 'family', 'plant_class', 'division')
    list_filter = ('order', 'family', 'plant_class', 'division')
    search_fields = ('name', 'scientific_name', 'description')

admin.site.register(Plant, PlantAdmin)
