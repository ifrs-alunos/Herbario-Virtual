from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='view_dashboard'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
]