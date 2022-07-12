from django.db import models
from django.contrib.auth import get_user_model
from herbarium.models import Plant


class PlantSolicitation(models.Model):
    """Essa classe define uma solicitação de uma nova planta por um contribuidor"""
    
    class Status(models.TextChoices):
        SENT = ('sent', 'Em análise')
        ACCEPTED = ('accepted', 'Aceita')
        DENIED = ('denied', 'Negada')

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Usuário', related_name="plants_solicitations")
    date = models.DateField(verbose_name="Data de envio", auto_now_add=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.SENT)
    new_plant = models.ForeignKey(Plant, on_delete=models.CASCADE, verbose_name='Nova Planta', related_name="+")

    def __str__(self):
        return 'Solicitação: {}'.format(self.user)

    class Meta:
        verbose_name = 'Solicitação de planta'
        verbose_name_plural = 'Solicitações de plantas'
        ordering = ['id']
