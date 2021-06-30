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
    path('trocar-senha', views.ChangePassword.as_view(), name="change_password"),
    path('contribuicoes', views.ContributionTemplateView.as_view(), name="contributions"),
    path('atualizar-herbario/', views.HerbariumListView.as_view(), name="herbarium_update"),
    path('lista-usuarios/', views.UserListView.as_view(), name="user_list"),
    path('solicitacao-de-planta/', views.plant_solicitation, name="plant_solicitation"),
    path('solicitacao-de-foto/', views.photo_solicitation, name="photo_solicitation"),
    path('solicitacoes-plantas/', views.PlantSolicitationListView.as_view(), name="plant_solicitation_list"),
    path('solicitacoes-fotos/', views.PhotoSolicitationListView.as_view(), name="photo_solicitation_list"),
]