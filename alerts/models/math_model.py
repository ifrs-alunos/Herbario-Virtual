from django.db import models
from .base import BaseModel


class MathModel(BaseModel):
    name = models.CharField('Nome do modelo matemático', max_length=100, blank=False,
                            help_text='Insira o nome do modelo matemático')
    source_code = models.TextField(max_length=1000)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Modelo matemático'
        verbose_name_plural = 'Modelos matemáticos'
