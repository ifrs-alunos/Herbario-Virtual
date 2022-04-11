from django.db import models

from disease.models.disease import Disease


class Constant(models.Model):
    """Esta classe define os dados de uma constante da doença."""
    nome = models.CharField("Nome", max_length=100)
    value = models.IntegerField(verbose_name="Valor")
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Constante'
        verbose_name_plural = 'Constantes'
