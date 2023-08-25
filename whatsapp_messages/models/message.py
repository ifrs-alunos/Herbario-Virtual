from django.db import models

class Message(models.Model):
	"""Classe que refere-se a cada mensagem enviada pelo LabFito por Whatsapp"""
	sender_number = models.CharField(verbose_name="Número do sistema que enviou a mensagem", max_length=13)
	receiver_name = models.CharField(verbose_name="Nome de quem recebeu a mensagem", max_length=200)
	receiver_number = models.CharField(verbose_name="Número de quem recebeu a mensagem", max_length=13)
	timestamp = models.IntegerField(verbose_name="Timestamp (Data)")
	message_text = models.TextField(verbose_name="Texto da mensagem")
	message_id = models.CharField(verbose_name="Id da mensagem", default="", max_length=200)
	status_log = models.TextField(verbose_name="Atualização dos status desta mensagem", default="")


	def __str__(self):
		return f"{self.receiver_name} - {self.message_text}"

