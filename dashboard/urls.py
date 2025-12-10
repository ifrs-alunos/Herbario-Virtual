from django.urls import path
from django.contrib.auth import views as auth_views
from .views.management_views import *
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Autenticação e perfil
    path('criar/', views.create_user, name='create'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('sobre/', views.InfoView.as_view(), name='info'),
    path('trocar-senha', views.ChangePassword.as_view(), name="change_password"),
    path('checar-senha/', views.term_check_password, name="term_check_password"),

    # Dashboard principal
    path('', views.DashboardView.as_view(), name='view_dashboard'),

    # Solicitações
    path('solicitacao/', views.SolicitationCreateView.as_view(), name='solicitation'),
    path('lista-solicitacoes/', views.SolicitationListView.as_view(), name='solicitation_list'),
    path('solicitacao/<int:pk>/', views.SolicitationUpdateView.as_view(), name="solicitation_update"),
    path('aceitar-solicitacao/<int:pk>', views.accept_solicitation, name="accept_solicitation"),

    # Herbário e plantas
    path('editar-herbario/', views.HerbariumListView.as_view(), name="herbarium_update"),
    path('editar-planta/<int:pk>', views.plant_update, name="plant_update"),
    path('solicitacao-de-planta/', views.plant_solicitation, name="plant_solicitation"),
    path('solicitacoes-plantas/', views.PlantSolicitationListView.as_view(), name="plant_solicitation_list"),
    path('detalhes-planta/<slug:slug>/', views.PlantDetailView.as_view(), name='detail-plant'),
    path('apagar-planta/<slug:slug>/', views.PlantDeleteView.as_view(), name="delete_plant"),

    # Doenças
    path('editar-fitopatologico/', views.DiseaseListView.as_view(), name="disease_update"),
    path('editar-de-doenca/<int:pk>', views.disease_update, name="disease_update"),
    path('solicitacao-de-doenca/', views.disease_solicitation, name="disease_solicitation"),
    path('solicitacoes-doencas/', views.DiseaseSolicitationListView.as_view(), name="disease_solicitation_list"),
    path('detalhes-doencas/<slug:slug>/', views.DiseaseDetailView.as_view(), name='detail-disease'),
    path('apagar-doenca/<slug:slug>/', views.DiseaseDeleteView.as_view(), name="delete_disease"),

    # Fotos
    path('solicitacao-de-foto-planta/', views.photo_solicitation, name="photo_solicitation"),
    path('solicitacao-de-foto-doenca/', views.disease_photo_solicitation, name="disease_photo_solicitation"),
    path('solicitacoes-fotos-plantas/', views.PhotoSolicitationListView.as_view(), name="photo_solicitation_list"),
    path('solicitacoes-fotos-doencas/', views.DiseasePhotoSolicitationListView.as_view(),
         name="disease_photo_solicitation_list"),

    # Culturas
    path('adicionar-cultura/', views.culture_solicitation, name="culture_solicitation"),
    path('lista-culturas/', views.CultureListView.as_view(), name="culture_list"),
    path('editar-cultura/<int:pk>', views.culture_update, name="culture_update"),
    path('apagar-cultura/<slug:slug>', views.CultureDeleteView.as_view(), name="delete_culture"),

    # Publicações
    path('editar-publicacoes/', views.PublicationListView.as_view(), name="publication_update"),
    path('editar-de-publicacao/<int:pk>', views.publication_update, name="publication_update"),
    path('solicitacao-de-publi/', views.PublicationCreateView.as_view(), name="publication_add"),
    path('solicitacao-foto-publi/', views.publication_photo_solicitation, name="publication_photo_add"),
    path('apagar-publicacao/<int:pk>/', views.PublicationDeleteView.as_view(), name="delete_publication"),

    # Usuários
    path('lista-usuarios/', views.UserListView.as_view(), name="user_list"),
    path('detalhes-usuario/<int:pk>/', views.UserDetailView.as_view(), name='detail-user'),
    path('apagar-usuario/<int:pk>/', views.ProfileDeleteView.as_view(), name="delete_user"),

    # Sistema de Alertas - GESTÃO
    path('estacoes/', StationListView.as_view(), name='station_list'),
    path('estacoes/adicionar/', StationCreateView.as_view(), name='station_add'),
    path('estacoes/editar/<int:pk>/', StationUpdateView.as_view(), name='station_edit'),
    path('estacoes/excluir/<int:pk>/', StationDeleteView.as_view(), name='station_delete'),
    
    path('constantes/', ConstantListView.as_view(), name='constant_list'),
    path('constantes/adicionar/', ConstantCreateView.as_view(), name='constant_add'),
    path('constantes/editar/<int:pk>/', ConstantUpdateView.as_view(), name='constant_edit'),
    path('constantes/excluir/<int:pk>/', ConstantDeleteView.as_view(), name='constant_delete'),
    
    path('requisitos/', RequirementListView.as_view(), name='requirement_list'),
    path('requisitos/adicionar/', RequirementCreateView.as_view(), name='requirement_add'),
    path('requisitos/editar/<int:pk>/', RequirementUpdateView.as_view(), name='requirement_edit'),
    path('requisitos/excluir/<int:pk>/', RequirementDeleteView.as_view(), name='requirement_delete'),
    
    path('alertas/', AlertHistoryListView.as_view(), name='alert_history'),
    
    # Sistema de Alertas - MODELOS MATEMÁTICOS
    path('editar-modelos/', views.MathModelListView.as_view(), name="mathmodel_update"),
    path('adicionar-modelo/', views.CreateMathModel.as_view(), name="mathmodel_add"),
    path('editar-modelo/<int:pk>', views.UpdateMathModel.as_view(), name="mathmodel_edit"),
    path('deletar-modelo/<int:pk>', views.DeleteMathModel.as_view(), name="mathmodel_delete"),
    path('modelo/<int:mathmodel_id>/estacao/<int:station_id>/resultados/', 
         views.MathModelResultsView.as_view(), name='mathmodel_results'),

    # Sensores
    path('lista-sensores', views.SensorListView.as_view(), name="sensor_list"),
    path('editar-sensores-humanos/', views.SensorHumanListView.as_view(), name="sensor_human_update"),
    path('adicionar-sensor-humano/<int:pk>', views.create_sensor_human, name="sensor_human_add"),

    # Telegram
    path('telegram-alertas/', TelegramSubscriptionView.as_view(), name="telegram_subscription"),
    
    # Alertas Manuais
    path('alerta-manual/', ManualAlertView.as_view(), name='manual_alert'),

    # Contribuições
    path('contribuicoes', views.ContributionTemplateView.as_view(), name="contributions"),

    # Deleções de solicitações
    path('apagar-solicitacao/<int:pk>/', views.SolicitationDeleteView.as_view(), name="delete_solicitation"),
    path('apagar-solicitacao-planta/<int:pk>', views.PlantSolicitationDeleteView.as_view(),
         name="delete_plant_solicitation"),
    path('apagar-solicitacao-doenca/<int:pk>', views.DiseaseSolicitationDeleteView.as_view(),
         name="delete_diesase_solicitation"),
    path('apagar-solicitacao-foto-doenca/<int:pk>', views.DiseasePhotoSolicitationDeleteView.as_view(),
         name="delete_diesase_photo_solicitation"),
    path('apagar-solicitacao-foto-planta/<int:pk>', views.PlantPhotoSolicitationDeleteView.as_view(),
         name="delete_plant_photo_solicitation"),

    # Detalhes de solicitações
    path('detalhes-solicitacao-doenca/<int:pk>/', views.DiseaseSolicitationDetailView.as_view(),
         name='detail-solicitation-disease'),
    path('detalhes-solicitacao-planta/<int:pk>/', views.PlantSolicitationDetailView.as_view(),
         name='detail-solicitation-plant'),
    path('detalhes-solicitacao-foto-planta/<int:pk>/', views.PlantPhotoSolicitationDetailView.as_view(),
         name='detail-solicitation-plant-photo'),
    path('detalhes-solicitacao-foto-doenca/<int:pk>/', views.DiseasePhotoSolicitationDetailView.as_view(),
         name='detail-solicitation-disease-photo'),

    # Aceitações específicas
    path('aceitar-solicitacao-planta/<int:pk>', views.accept_plant_solicitation, name="accept_plant"),
    path('aceitar-solicitacao-doenca/<int:pk>', views.accept_disease_solicitation, name="accept_disease"),
    path('aceitar-solicitacao-foto-planta/<int:pk>', views.accept_plant_photo_solicitation, name="accept_plant_photo"),
    path('aceitar-solicitacao-foto-doenca/<int:pk>', views.accept_disease_photo_solicitation,
         name="accept_disease_photo"),
]