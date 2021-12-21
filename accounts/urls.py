from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path('criar/', views.create_user, name='create'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    # path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('sobre/', views.InfoView.as_view(), name='info'),

    path('', views.DashboardView.as_view(), name='view_dashboard'),
    path('perfil/', views.update_profile, name='profile'),
    path('solicitacao/', views.SolicitationCreateView.as_view(), name='solicitation'),
    path('lista-solicitacoes/', views.SolicitationListView.as_view(), name='solicitation_list'),
    path('solicitacao/<int:pk>/', views.SolicitationUpdateView.as_view(), name="solicitation_update"),
    path('trocar-senha', views.ChangePassword.as_view(), name="change_password"),
    path('contribuicoes', views.ContributionTemplateView.as_view(), name="contributions"),
    path('atualizar-herbario/', views.HerbariumListView.as_view(), name="herbarium_update"),
    path('atualizar-planta/<int:pk>', views.plant_update, name="plant_update"),
    path('lista-usuarios/', views.UserListView.as_view(), name="user_list"),
    path('solicitacao-de-planta/', views.plant_solicitation, name="plant_solicitation"),
    path('solicitacao-de-doenca/', views.disease_solicitation, name="disease_solicitation"),
    path('adicionar-modelo-matematico/', views.math_model_solicitation, name="math_model_solicitation"),
    path('atualizar-modelo-matematico/', views.MathModelsListView.as_view(), name="math_model_list"),
    path('atualizacao-de-doenca/<int:pk>', views.disease_update, name="disease_update"),
    path('solicitacao-caracteristicas/', views.disease_char_solicitation, name="disease_char_solicitation"),
    path('caracteristicas-fitopatologico/', views.CharListView.as_view(), name="char_phytopathological"),
    path('detalhes-caracteristica/<slug:slug>/', views.CharDetailView.as_view(), name='detail-char'),
    path('atualizar-fitopatologico/', views.DiseaseListView.as_view(), name="disease_update"),
    path('atualizar-caracteristica/<int:pk>', views.char_update, name="char_update"),
    path('atualizar-cultura/<int:pk>', views.culture_update, name="culture_update"),
    path('apagar-doenca/<slug:slug>/', views.DiseaseDeleteView.as_view(), name="delete_disease"),
    path('apagar-planta/<slug:slug>/', views.PlantDeleteView.as_view(), name="delete_plant"),
    path('apagar-caracteristica/<slug:slug>/', views.CharDeleteView.as_view(), name="delete_char"),
    path('detalhes-doencas/<slug:slug>/', views.DiseaseDetailView.as_view(), name='detail-disease'),
    path('detalhes-solicitacao-doenca/<int:pk>/', views.DiseaseSolicitationDetailView.as_view(), name='detail-solicitation-disease'),
    path('detalhes-planta/<slug:slug>/', views.PlantDetailView.as_view(), name='detail-plant'),
    path('solicitacao-de-foto-planta/', views.photo_solicitation, name="photo_solicitation"),
    path('solicitacao-de-foto-doenca/', views.disease_photo_solicitation, name="disease_photo_solicitation"),
    path('solicitacoes-plantas/', views.PlantSolicitationListView.as_view(), name="plant_solicitation_list"),
    path('solicitacoes-doencas/', views.DiseaseSolicitationListView.as_view(), name="disease_solicitation_list"),
    path('solicitacoes-fotos-plantas/', views.PhotoSolicitationListView.as_view(), name="photo_solicitation_list"),
    path('adicionar-cultura/', views.culture_solicitation, name="culture_solicitation"),
    path('lista-culturas/', views.CultureListView.as_view(), name="culture_list"),
    path('apagar-cultura/<slug:slug>', views.CultureDeleteView.as_view(), name="delete_culture"),

]