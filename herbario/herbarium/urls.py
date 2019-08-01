from django.urls import path

from . import views

app_name = 'herbarium'
urlpatterns = [
    path('', views.index, name='index'),
    path('detalhes/<slug:slug>/', views.detail, name='detail'),

]
