from accounts.models import solicitation
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='view_dashboard'),
    path('perfil/', views.update_profile, name='profile'),
    path('solicitacao/', views.SolicitationCreateView.as_view(), name='solicitation'),
    path('lista-solicitacoes/', views.SolicitationListView.as_view(), name='solicitation_list'),
    path('solicitacao/<int:pk>/', views.SolicitationUpdateView.as_view(), name="solicitation_update"),
]