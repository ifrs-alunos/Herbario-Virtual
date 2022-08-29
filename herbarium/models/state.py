from django.db import models
from .region import Region


class State(models.Model):
    """Esta classe define um estado (unidade federativa) que pertence à uma região"""

    name = models.CharField('Nome', blank=False, max_length=20)
    initials = models.CharField('Sigla', blank=False, max_length=2, null=True)

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="states", null=True,
                               verbose_name="Região")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['name']
