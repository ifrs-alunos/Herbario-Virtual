from django.db import models

from whatsapp_messages.functions import send_whatsapp_message


class UserAlert(models.Model):
    profile = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, verbose_name="Usuário"
    )
    disease = models.ForeignKey(
        "disease.Disease", on_delete=models.CASCADE, verbose_name="Doença"
    )

    def __str__(self):
        return f"{self.profile} - {self.disease}"

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"

    def send_alert(self):
        send_whatsapp_message(self.profile.phone, "Alerta de doença: " + self.disease.name_disease)
