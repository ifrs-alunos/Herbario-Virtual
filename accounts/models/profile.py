from django.db import models
from django.contrib.auth.models import User

from whatsapp_messages.functions import send_telegram_message
from .solicitation import Solicitation


class Profile(models.Model):
    """Essa classe define um perfil de um usuário"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200,
        verbose_name="Nome completo",
        help_text="Não utilize abreviações nos sobrenomes.",
    )
    institution = models.CharField(
        max_length=150,
        verbose_name="Instituição de trabalho e/ou estudo",
        help_text="Caso possuia mais de uma, escreva a que atua principalmente.",
    )
    role = models.CharField(
        max_length=100,
        verbose_name="Cargo de ofício",
        help_text="Utilize como base seu cargo na instituição citada.",
    )
    phone = models.CharField(
        unique=True,
        max_length=11,
        verbose_name="Telefone fixo ou celular",
        help_text="Informe o DDD e, em seguida, seu número.",
    )
    cpf = models.CharField(
        max_length=11,
        verbose_name="CPF",
        help_text="Informe o CPF somente com números.",
    )
    rg = models.CharField(max_length=10, verbose_name="RG")

    alerts_for_diseases = models.ManyToManyField("disease.Disease", verbose_name="alertas para doenças", blank=True)

    def __str__(self):
        return self.name

    def send_alert(self, disease):
        """Envia alerta para o usuário"""
        send_telegram_message(self.messageconfirmation.telegram_chat_id, "Alerta de doença: " + disease.name_disease)

    def can_send_solicitation(self):
        # Selecionando solicitações de um usuário
        solicitations = self.user.solicitations

        # Filtrando as solicitações enviadas
        sends = solicitations.filter(status=Solicitation.Status.SENT)
        accepteds = solicitations.filter(status=Solicitation.Status.ACCEPTED)

        if sends.exists() or accepteds.exists():
            # Não envia solicitação caso existam aceitas ou enviadas
            return False
        else:
            # Envia solicitação caso não tenha enviado ou todas sejam rejeitadas
            return True

    def can_get_messages(self):
        self.get_messages = True
        self.save()
