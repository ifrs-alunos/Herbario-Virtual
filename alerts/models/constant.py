from django.db import models
from .base import BaseModel

class Constant(BaseModel):
    """Esta classe define os dados de uma constante da doença."""
    name = models.CharField("Nome", max_length=100)
    value = models.FloatField(verbose_name="Valor")
    mathmodel = models.ForeignKey('MathModel', on_delete=models.CASCADE, null=True)
    description = models.TextField(
        "Descrição",
        blank=True,
        help_text="Descrição da constante"
    )

    def __str__(self):
        return f"{self.name} - {self.mathmodel}"

    class Meta:
        verbose_name = "Constante"
        verbose_name_plural = "Constantes"
        managed = True