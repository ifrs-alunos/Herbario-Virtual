from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path('criar/', views.create_user, name='create'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    # path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
]