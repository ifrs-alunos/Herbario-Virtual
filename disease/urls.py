from django.urls import path

from . import views

app_name = 'disease'

urlpatterns = [
    path('', views.DiseaseIndex.as_view(), name='disease'),
    path('<slug:culture>/', views.DiseaseIndex.as_view(), name="diseases"),
]

