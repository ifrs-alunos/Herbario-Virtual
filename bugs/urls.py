from django.urls import path

from . import views

app_name = 'bugs'
urlpatterns = [
    path('', views.bugsIndex.as_view(), name='index'),
    # path('detalhes/<slug:slug>/', views.HerbariumDetail.as_view(), name='detail'),
    # Página de detalhe de um inseto em específico
    path('detalhes/<slug:slug>/', views.bugsDetail.as_view(), name='detail'),
    # Página de listagem de insetos

    path('<slug:family>/', views.bugsIndex.as_view(), name="bugs"),  
]

