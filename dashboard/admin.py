from django.contrib import admin

from .models import DiseaseSolicitation, DiseasePhotoSolicitation, PhotoSolicitation, PlantSolicitation

admin.site.register(DiseaseSolicitation)
admin.site.register(DiseasePhotoSolicitation)
admin.site.register(PhotoSolicitation)
admin.site.register(PlantSolicitation)