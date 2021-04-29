from accounts.models import solicitation
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='view_dashboard'),
    path('perfil/', views.update_profile, name='profile'),
    path('solicitacao/', views.SendSolicitation.as_view(), name='solicitation'),
]