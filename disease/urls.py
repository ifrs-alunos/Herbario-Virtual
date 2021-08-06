from django.urls import path

from . import views

app_name = 'disease'

urlpatterns = [
    path('', views.DiseaseIndex, name='disease'),
]

