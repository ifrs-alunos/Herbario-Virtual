from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path('criar/', views.create_user, name='criar_conta'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
]