from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('saiba-mais/<str:highlight_slug>', views.highlight, name='highlight'),
    path('disciplinas', views.subjects, name='subjects'),
    path('colaboradores', views.ColaboratorsListView.as_view(), name='about'),
    path('editar-colaboradores', views.colaborators_edit, name='edit-about'),
    path('materiais', views.BookListView.as_view(), name='content'),
    path('materiais/<slug:content>/', views.BookListView.as_view(), name='contents'),
    path('publicacoes', views.PublicationListView.as_view(), name='publications'),
    path('publicacao/<slug:slug>', views.PublicationDetail.as_view(), name='publication-detail'),
    
]
