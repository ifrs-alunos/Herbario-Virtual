from django.db import models
from django.contrib.auth import get_user_model

class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name="Nome completo")
    institution = models.CharField(max_length=150, verbose_name="Instituição de trabalho e/ou estudo")
    role = models.CharField(max_length=100, verbose_name="Cargo de ofício", help_text="Utilize como base seu cargo na instituição citada.")
    phone = models.CharField(max_length=11, verbose_name="Telefone fixo ou celular")
