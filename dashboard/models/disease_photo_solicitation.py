from django.db import models
from django.contrib.auth import get_user_model
from disease.models import PhotoDisease


class DiseasePhotoSolicitation(models.Model):
    """Essa classe define uma solicitação de uma nova foto de doença por um contribuidor"""

    class Status(models.TextChoices):
        SENT = ('sent', 'Em análise')
        ACCEPTED = ('accepted', 'Aceita')
        DENIED = ('denied', 'Negada')

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Usuário',
                             related_name="disease_photo_solicitations",null=True)
    date = models.DateField(verbose_name="Data de envio", auto_now_add=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.SENT)
    new_photo = models.ForeignKey(PhotoDisease, on_delete=models.CASCADE, verbose_name='Nova Foto',null=True)

    def __str__(self):
        return 'Solicitação: {}'.format(self.user)

    class Meta:
        verbose_name = 'Solicitação de foto'
        verbose_name_plural = 'Solicitações de fotos'
        ordering = ['id']
