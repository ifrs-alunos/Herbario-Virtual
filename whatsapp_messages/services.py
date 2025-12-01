import logging
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Serviço para envio de mensagens via WhatsApp utilizando a API da Twilio.
    """

    def __init__(self):
        """Inicializa o cliente Twilio com credenciais."""
        try:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID, 
                settings.TWILIO_AUTH_TOKEN
            )
            logger.info("Cliente Twilio inicializado com sucesso")
        except Exception as e:
            logger.critical(f"Falha ao inicializar Twilio: {str(e)}")
            raise

    def _formatar_numero(self, numero: str) -> str:
        """Formata o número para o padrão internacional (E.164)."""
        if not numero:
            raise ValidationError("Número de telefone não fornecido")
            
        numero = numero.strip().replace(" ", "").replace("-", "")
        
        if numero.startswith("+"):
            return f"whatsapp:{numero}"
            
        if not numero.startswith("55"):
            numero = f"55{numero}"
            
        return f"whatsapp:+{numero}"

    def enviar_mensagem(self, mensagem_obj) -> bool:
        """Envia mensagem via WhatsApp e atualiza o status."""
        try:
            from .models import Message  # Importação local para evitar circularidade
            
            if not mensagem_obj.receiver or not mensagem_obj.message_text:
                raise ValidationError("Dados incompletos para envio")
                
            numero_destino = self._formatar_numero(mensagem_obj.receiver.phone)
            
            mensagem_twilio = self.client.messages.create(
                body=mensagem_obj.message_text,
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=numero_destino,
                status_callback=f"{settings.BASE_URL}/whatsapp/status/"
            )
            
            mensagem_obj.external_id = mensagem_twilio.sid
            mensagem_obj.status = 'enviada'
            mensagem_obj.detalhes_envio = {
                'provedor': 'twilio',
                'hora_envio': mensagem_twilio.date_created.isoformat(),
                'custo': mensagem_twilio.price
            }
            mensagem_obj.save()
            
            logger.info(f"Mensagem {mensagem_obj.id} enviada para {numero_destino}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio: {e.code} - {e.msg}")
            self._atualizar_falha(mensagem_obj, str(e))
            return False
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            self._atualizar_falha(mensagem_obj, str(e))
            return False

    def _atualizar_falha(self, mensagem_obj, erro: str):
        """Atualiza o status da mensagem como falha."""
        mensagem_obj.status = 'falha'
        mensagem_obj.erro = erro[:200]
        mensagem_obj.save()

def enviar_alerta_whatsapp(phone, message):
    """Função simplificada para envio de alertas"""
    service = WhatsAppService()
    return service.enviar_mensagem_simples(phone, message)

def enviar_mensagem_simples(self, phone, text):
        """Versão simplificada para envio direto sem objeto Message"""
        try:
            numero_destino = self._formatar_numero(phone)
            self.client.messages.create(
                body=text,
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=numero_destino
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem simples: {str(e)}")
            return False