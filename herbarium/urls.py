from django.urls import path

from . import views

app_name = 'herbarium'
urlpatterns = [
    path('', views.HerbariumIndex.as_view(), name='index'),
    # path('detalhes/<slug:slug>/', views.HerbariumDetail.as_view(), name='detail'),
    # Página de detalhe de uma planta em específico
    path('detalhes/<slug:slug>/', views.HerbariumDetail.as_view(), name='detail'),
    # Página de listagem de plantas

    path('<slug:family>/', views.HerbariumIndex.as_view(), name="plants"),  
]

