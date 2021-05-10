from django.db import models
from django.contrib.auth import get_user_model

class Solicitation(models.Model):
    """Essa classe define uma solicitação para um usuário comum se tornar contribuidor do sistema"""
    
    class Status(models.TextChoices):
        SENT = ('sent', 'Em análise')
        ACCEPTED = ('accepted', 'Aceita')
        DENIED = ('denied', 'Negada')

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Usuário', related_name="solicitations")
    message = models.TextField(verbose_name="Mensagem")
    date = models.DateField(verbose_name="Data de envio", auto_now_add=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.SENT)

    def __str__(self):
        return 'Solicitação: {}'.format(self.user)

    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
        ordering = ['id']
