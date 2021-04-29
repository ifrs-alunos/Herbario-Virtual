from django.db import models
from django.contrib.auth import get_user_model

class Solicitation(models.Model):
    class Status(models.TextChoices):
        SENT = ('sent', 'Enviado')
        ACCEPTED = ('accepted', 'Aceito')
        DENIED = ('denied', 'Negado')

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Usuário')
    message = models.TextField(verbose_name="Mensagem")
    date = models.DateField(verbose_name="Data de envio", auto_now_add=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.SENT)

    def __str__(self):
        return 'Solicitação: {}'.format(self.user)

    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
