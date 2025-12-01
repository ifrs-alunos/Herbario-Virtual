import json
import logging
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView, View, ListView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib import messages as django_messages
from django.conf import settings
from .models import Message, MessageConfirmation, TelegramSubscription
from .forms import AlertPreferencesForm
from disease.models import Disease

logger = logging.getLogger(__name__)

class WhatsAppAlertPreferencesView(LoginRequiredMixin, FormView):
    template_name = 'whatsapp_messages/alert_preferences.html'
    form_class = AlertPreferencesForm
    success_url = reverse_lazy('whatsapp_messages:alert_preferences')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            profile = self.request.user.profile
            
            profile.whatsapp_enabled = form.cleaned_data['whatsapp_enabled']
            profile.telegram_enabled = form.cleaned_data['telegram_enabled']
            profile.phone = form.cleaned_data['phone']
            profile.save()
            
            profile.alerts_for_diseases.set(form.cleaned_data['diseases'])
            
            django_messages.success(self.request, "Preferências de alerta atualizadas com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao salvar preferências: {e}")
            django_messages.error(self.request, "Erro ao salvar preferências.")
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['diseases'] = Disease.objects.all()
        context['has_telegram'] = hasattr(self.request.user, 'profile') and \
                                 hasattr(self.request.user.profile, 'message_confirmation') and \
                                 self.request.user.profile.message_confirmation.telegram_chat_id
        return context

class AlertsForDiseasesView(LoginRequiredMixin, ListView):
    model = Disease
    template_name = 'whatsapp_messages/alerts_for_diseases.html'
    context_object_name = 'diseases'

    def get_queryset(self):
        return Disease.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'profile'):
            context['selected_diseases'] = self.request.user.profile.alerts_for_diseases.all()
        else:
            context['selected_diseases'] = Disease.objects.none()
        return context

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Recebe webhooks do provedor de WhatsApp"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            message_sid = data.get('MessageSid')
            
            if message_sid:
                message = Message.objects.get(external_id=message_sid)
                status = data.get('MessageStatus')
                
                if status == 'delivered':
                    message.update_status('delivered')
                elif status == 'read':
                    message.update_status('read')
                elif status == 'failed':
                    message.update_status('failed', {
                        'error_code': data.get('ErrorCode'),
                        'error_message': data.get('ErrorMessage')
                    })
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Erro no webhook WhatsApp: {e}")
            return JsonResponse({'status': 'error'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class SetTelegramWebhookView(View):
    """View para configurar o webhook do Telegram"""
    
    def get(self, request):
        try:
            webhook_url = f"{settings.BASE_URL}/whatsapp_messages/telegram/webhook/"
            telegram_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
            
            if not telegram_token:
                return JsonResponse({'status': 'error', 'message': 'Token do Telegram não configurado'}, status=400)
            
            response = requests.get(
                f"https://api.telegram.org/bot{telegram_token}/setWebhook",
                params={'url': webhook_url}
            )
            return JsonResponse(response.json())
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def telegram_webhook(request):
    """Endpoint para receber atualizações do Telegram"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Dados recebidos do Telegram: {data}")
            
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                text = message.get('text', '').strip()
                username = message['from'].get('username', '')
                first_name = message['from'].get('first_name', '')
                
                if text == '/start':
                    subscription, created = TelegramSubscription.subscribe(
                        chat_id=chat_id,
                        username=username,
                        first_name=first_name
                    )
                    
                    response_text = (
                        "👋 Olá! Bem-vindo ao sistema de alertas!\n\n"
                        "✅ Você foi cadastrado para receber alertas sobre condições de doenças.\n\n"
                        "📊 Receberá notificações quando condições críticas forem detectadas.\n\n"
                        "❌ Use /stop para cancelar os alertas."
                    )
                    
                elif text == '/stop':
                    success = TelegramSubscription.unsubscribe(chat_id)
                    response_text = "❌ Você foi removido do sistema de alertas." if success else "⚠️ Você não estava cadastrado."
                    
                else:
                    response_text = (
                        "🤖 Comandos disponíveis:\n"
                        "/start - Cadastrar para receber alertas\n"
                        "/stop - Parar de receber alertas\n"
                        "/help - Ver esta mensagem"
                    )
                
                telegram_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
                if telegram_token:
                    requests.post(
                        f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                        json={
                            'chat_id': chat_id,
                            'text': response_text,
                            'parse_mode': 'Markdown'
                        }
                    )
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Erro no webhook Telegram: {e}")
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'method not allowed'}, status=405)

@csrf_exempt
def verify_whatsapp(request):
    """Verificação de número do WhatsApp"""
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            code = request.POST.get('code')
            
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'error', 'message': 'Usuário não autenticado'}, status=401)
            
            profile = request.user.profile
            confirmation, created = MessageConfirmation.objects.get_or_create(profile=profile)
            
            if confirmation.verify_code(code):
                profile.phone = phone
                profile.whatsapp_verified = True
                profile.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Código inválido ou expirado'}, status=400)
                
        except Exception as e:
            logger.error(f"Erro na verificação WhatsApp: {e}")
            return JsonResponse({'status': 'error', 'message': 'Erro interno'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)