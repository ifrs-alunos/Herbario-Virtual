from django.shortcuts import render
from django.urls import path
from . import views

# Create your views here.

app_name = 'bugs'

urlpatterns = [
    path('', views.index, name='index'),
    path('detail/', views.detail, name='detail'),
    path('pagination/', views.pagination, name='pagination'),
]