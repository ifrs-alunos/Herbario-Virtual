from django.urls import path

from . import views

app_name = 'disease'

urlpatterns = [
    path('', views.DiseaseIndex.as_view(), name='disease'),
    path('detalhes/<slug:slug>/', views.DiseaseDetail.as_view(), name='disease-detail'),
    path('<slug:culture_disease>/', views.DiseaseIndex.as_view(), name="diseases"),
]

