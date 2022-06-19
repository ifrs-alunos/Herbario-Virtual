from accounts.models.solicitation import Solicitation
from django.contrib import admin
from .models import Solicitation, Profile, PhotoSolicitation, PlantSolicitation, DiseaseSolicitation, Characteristic,\
	CharSolicitationModel, DiseasePhotoSolicitation

# Register your models here.

admin.site.register(Solicitation)
admin.site.register(Profile)
admin.site.register(PlantSolicitation)
admin.site.register(PhotoSolicitation)
admin.site.register(DiseaseSolicitation)
admin.site.register(CharSolicitationModel)
admin.site.register(DiseasePhotoSolicitation)
