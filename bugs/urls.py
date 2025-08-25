from django.shortcuts import render
from django.urls import path
from . import views

# Create your views here.

app_name = 'bugs'

urlpatterns = [
    path('', views.home, name='index'),
    path('detalhes/', views.detail, name='detail'),
    path('pagination/', views.pagination, name='pagination'),
]