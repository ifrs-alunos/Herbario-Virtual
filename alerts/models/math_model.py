from django.db import models

from . import Station
from .base import BaseModel
from disease.models.disease import Disease

class MathModel(BaseModel):
    name = models.CharField('Nome do modelo matemático', max_length=100, blank=False,
                            help_text='Insira o nome do modelo matemático')
    source_code = models.TextField(max_length=1000, help_text="Variaveis disponiveis no momento: t = Temperatura rh = "
                                                              "Umidade Relativa</h4>")
    disease = models.ForeignKey(Disease, verbose_name="Doença", on_delete=models.PROTECT)
    stations = models.ManyToManyField(Station, verbose_name="Estaçôes atreladas", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Modelo matemático'
        verbose_name_plural = 'Modelos matemáticos'

