from django.db import models
from . profile import Profile


class Contribuition(models.Model):
    """Essa classe especifica os dados referentes a uma contribuição"""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="contribuitions",
                                verbose_name="Perfil")
