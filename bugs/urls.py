from django.shortcuts import render
from django.urls import path
from . import views

# Create your views here.

app_name = 'bugs'

urlpatterns = [
    path('', views.index, name='bugs'),
    path('detalhes/<slug:culture>/<slug:slug>/', views.DiseaseDetail.as_view(), name='disease-detail'),
    path('<slug:culture_disease>/', views.DiseaseIndex.as_view(), name="diseases"),
]