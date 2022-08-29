from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dashboard'


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
    path('checar-senha/', views.term_check_password, name="term_check_password"),
    path('editar-herbario/', views.HerbariumListView.as_view(), name="herbarium_update"),
    path('editar-planta/<int:pk>', views.plant_update, name="plant_update"),
    path('lista-usuarios/', views.UserListView.as_view(), name="user_list"),
    path('solicitacao-de-planta/', views.plant_solicitation, name="plant_solicitation"),
    path('solicitacao-de-doenca/', views.disease_solicitation, name="disease_solicitation"),
    path('editar-de-doenca/<int:pk>', views.disease_update, name="disease_update"),
    path('detalhes-usuario/<int:pk>/', views.UserDetailView.as_view(), name='detail-user'),
    path('editar-fitopatologico/', views.DiseaseListView.as_view(), name="disease_update"),
    path('editar-cultura/<int:pk>', views.culture_update, name="culture_update"),
    path('aceitar-solicitacao-planta/<int:pk>', views.accept_plant_solicitation, name="accept_plant"),
    path('aceitar-solicitacao-doenca/<int:pk>', views.accept_disease_solicitation, name="accept_disease"),
    path('aceitar-solicitacao-foto-planta/<int:pk>', views.accept_plant_photo_solicitation, name="accept_plant_photo"),
    path('aceitar-solicitacao-foto-doenca/<int:pk>', views.accept_disease_photo_solicitation, name="accept_disease_photo"),
    path('aceitar-solicitacao/<int:pk>', views.accept_solicitation, name="accept_solicitation"),
    path('apagar-doenca/<slug:slug>/', views.DiseaseDeleteView.as_view(), name="delete_disease"),
    path('apagar-planta/<slug:slug>/', views.PlantDeleteView.as_view(), name="delete_plant"),
    path('apagar-solicitacao/<int:pk>/', views.SolicitationDeleteView.as_view(), name="delete_solicitation"),
    path('apagar-usuario/<int:pk>/', views.ProfileDeleteView.as_view(), name="delete_user"),
    path('detalhes-doencas/<slug:slug>/', views.DiseaseDetailView.as_view(), name='detail-disease'),
    path('detalhes-solicitacao-doenca/<int:pk>/', views.DiseaseSolicitationDetailView.as_view(), name='detail-solicitation-disease'),
    path('detalhes-solicitacao-planta/<int:pk>/', views.PlantSolicitationDetailView.as_view(), name='detail-solicitation-plant'),
    path('detalhes-solicitacao-foto-planta/<int:pk>/', views.PlantPhotoSolicitationDetailView.as_view(), name='detail-solicitation-plant-photo'),
    path('detalhes-solicitacao-foto-doenca/<int:pk>/', views.DiseasePhotoSolicitationDetailView.as_view(), name='detail-solicitation-disease-photo'),
    path('detalhes-planta/<slug:slug>/', views.PlantDetailView.as_view(), name='detail-plant'),
    path('solicitacao-de-foto-planta/', views.photo_solicitation, name="photo_solicitation"),
    path('solicitacao-de-foto-doenca/', views.disease_photo_solicitation, name="disease_photo_solicitation"),
    path('solicitacoes-plantas/', views.PlantSolicitationListView.as_view(), name="plant_solicitation_list"),
    path('solicitacoes-doencas/', views.DiseaseSolicitationListView.as_view(), name="disease_solicitation_list"),
    path('solicitacoes-fotos-plantas/', views.PhotoSolicitationListView.as_view(), name="photo_solicitation_list"),
    path('solicitacoes-fotos-doencas/', views.DiseasePhotoSolicitationListView.as_view(), name="disease_photo_solicitation_list"),
    path('adicionar-cultura/', views.culture_solicitation, name="culture_solicitation"),
    path('lista-culturas/', views.CultureListView.as_view(), name="culture_list"),
    path('apagar-cultura/<slug:slug>', views.CultureDeleteView.as_view(), name="delete_culture"),
    path('apagar-solicitacao-planta/<int:pk>', views.PlantSolicitationDeleteView.as_view(), name="delete_plant_solicitation"),
    path('apagar-solicitacao-doenca/<int:pk>', views.DiseaseSolicitationDeleteView.as_view(), name="delete_diesase_solicitation"),
    path('apagar-solicitacao-foto-doenca/<int:pk>', views.DiseasePhotoSolicitationDeleteView.as_view(), name="delete_diesase_photo_solicitation"),
    path('apagar-solicitacao-foto-planta/<int:pk>', views.PlantPhotoSolicitationDeleteView.as_view(), name="delete_plant_photo_solicitation"),
    path('editar-publicacoes/', views.PublicationListView.as_view(), name="publication_update"),
    path('editar-de-publicacao/<int:pk>', views.publication_update, name="publication_update"),
    path('solicitacao-de-publi/', views.PublicationCreateView.as_view(), name="publication_add"),
    path('apagar-publicacao/<int:pk>/', views.PublicationDeleteView.as_view(), name="delete_publication"),
    path('solicitacao-foto-publi/', views.publication_photo_solicitation, name="publication_photo_add"),
    path('editar-modelos/', views.MathModelListView.as_view(), name="mathmodel_update"),
    path('adicionar-modelo/', views.CreateMathModel.as_view(), name="mathmodel_add"),
    path('editar-modelo/<int:pk>', views.UpdateMathModel.as_view(), name="mathmodel_edit"),
    path('deletar-modelo/<int:pk>', views.DeleteMathModel.as_view(), name="mathmodel_delete"),
    path('editar-sensores-humanos/', views.SensorHumanListView.as_view(), name="sensor_human_update"),
    path('adicionar-sensor-humano/<int:pk>', views.create_sensor_human, name="sensor_human_add"),

]