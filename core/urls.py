from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('saiba-mais/<str:highlight_slug>', views.highlight, name='highlight'),
    path('subjects', views.subjects, name='subjects'),
    path('colaboradores', views.ColaboratorsListView.as_view(), name='about'),
    path('editar-colaboradores', views.colaborators_edit, name='edit-about')
]
