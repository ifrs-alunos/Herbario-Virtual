import logging
import asyncio
import threading
import time
import sys
from asgiref.sync import sync_to_async
import requests
from django.conf import settings
from django.utils import timezone

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.application = None
            cls._instance.started = False
        return cls._instance
    
    def __init__(self):
        if not self.started:
            self.started = True
            print("🚀 Inicializando TelegramBot...")
            self._start_bot()
    
    def _start_bot(self):
        """Inicia o bot com loop correto"""
        def run_bot():
            try:
                print("🟡 CONFIGURANDO LOOP DE EVENTOS...")
                
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                print("🟡 LOOP CONFIGURADO, IMPORTANDO BIBLIOTECAS...")
                
                from telegram.ext import Application, CommandHandler, MessageHandler, filters
                from config.settings import TELEGRAM_BOT_TOKEN
                
                print(f"🟡 TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...")
                
                print("🟡 CRIANDO APLICAÇÃO...")
                self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
                print("🟡 APLICAÇÃO CRIADA")
                
                print("🟡 CONFIGURANDO HANDLERS...")
                self.application.add_handler(CommandHandler("start", self._handle_start))
                self.application.add_handler(CommandHandler("stop", self._handle_stop))
                self.application.add_handler(CommandHandler("teste", self._handle_test))
                self.application.add_handler(MessageHandler(filters.ALL, self._handle_any_message))
                
                print("🟡 INICIANDO POLLING...")
                
                loop.run_until_complete(self._start_polling())
                
            except Exception as e:
                print(f"🔴 ERRO CRÍTICO NO BOT: {e}")
                import traceback
                traceback.print_exc()
        
        thread = threading.Thread(target=run_bot, daemon=True, name="TelegramBot")
        thread.start()
        print("✅ BOT INICIADO EM THREAD")
    
    async def _start_polling(self):
        """Inicia o polling"""
        try:
            print("🔄 INICIANDO POLLING...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            print("✅ BOT RODANDO E OUVINDO MENSAGENS!")
            print("🤖 Pronto para receber comandos...")
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"🔴 ERRO NO POLLING: {e}")
    
    async def _handle_any_message(self, update, context):
        """Handler para QUALQUER mensagem - para debug"""
        try:
            if update.message and update.message.text:
                print(f"📨 MENSAGEM RECEBIDA: '{update.message.text}'")
                print(f"📨 CHAT ID: {update.effective_chat.id}")
                print(f"📨 USUÁRIO: {update.effective_user.first_name}")
                print("---")
        except Exception as e:
            print(f"🔴 ERRO NO HANDLER GERAL: {e}")
    
    async def _handle_start(self, update, context):
        """Handler para /start"""
        try:
            print(f"🎯 /start RECEBIDO DE: {update.effective_user.first_name}")
            
            from telegram_bot.models import TelegramUser
            
            chat_id = update.effective_chat.id
            user = update.effective_user
            
            print(f"📝 CADASTRANDO USUÁRIO: {user.first_name} ({chat_id})")
            
            telegram_user, created = await sync_to_async(TelegramUser.subscribe)(
                chat_id=chat_id,
                username=user.username or "",
                first_name=user.first_name or ""
            )
            
            print(f"✅ USUÁRIO {'CADASTRADO' if created else 'REATIVADO'}")
            
            response = (
                "✅ *Cadastro realizado com sucesso!*\n\n"
                "Agora você receberá alertas meteorológicos importantes.\n\n"
                "Use /teste para ver um exemplo.\n"
                "Use /stop para cancelar inscrição."
            )
            
            await update.message.reply_text(response, parse_mode="Markdown")
            
            print(f"📤 RESPOSTA ENVIADA PARA: {user.first_name}")
            
        except Exception as e:
            print(f"🔴 ERRO NO /start: {e}")
            await update.message.reply_text("❌ Erro no cadastro. Tente novamente.")
    
    async def _handle_stop(self, update, context):
        """Handler para /stop"""
        try:
            print(f"🎯 /stop RECEBIDO DE: {update.effective_user.first_name}")
            
            from telegram_bot.models import TelegramUser
            
            chat_id = update.effective_chat.id
            success = await sync_to_async(TelegramUser.unsubscribe)(chat_id)
            
            if success:
                await update.message.reply_text("🔕 *Inscrição cancelada!*", parse_mode="Markdown")
                print(f"✅ USUÁRIO REMOVIDO: {chat_id}")
            else:
                await update.message.reply_text("❌ Você não estava cadastrado.")
                
        except Exception as e:
            print(f"🔴 ERRO NO /stop: {e}")
            await update.message.reply_text("❌ Erro ao cancelar.")
    
    async def _handle_test(self, update, context):
        """Handler para /teste"""
        try:
            print(f"🎯 /teste RECEBIDO DE: {update.effective_user.first_name}")
            
            await update.message.reply_text(
                "⚠️ *TESTE DE ALERTA METEOROLÓGICO* ⚠️\n\n"
                "🔸 *Evento:* Tempestade Severa\n"
                "🔸 *Intensidade:* Alta\n"
                "🔸 *Recomendação:* Procure abrigo\n\n"
                "✅ *Sistema funcionando corretamente!*",
                parse_mode="Markdown"
            )
            
            print(f"✅ TESTE ENVIADO PARA: {update.effective_user.first_name}")
            
        except Exception as e:
            print(f"🔴 ERRO NO /teste: {e}")
            await update.message.reply_text("❌ Erro no teste.")
    
    def enviar_alerta_sincrono(self, mensagem):
        """Envia alerta para todos os usuários"""
        try:
            print(f"🟡 TENTANDO ENVIAR ALERTA: {mensagem[:50]}...")
            
            if not self.application or not self.application.bot:
                print("🔴 BOT NÃO DISPONÍVEL PARA ENVIO")
                return False
            
            from telegram_bot.models import TelegramUser
            usuarios = TelegramUser.objects.filter(is_active=True)
            print(f"🟡 USUÁRIOS ATIVOS: {usuarios.count()}")
            
            enviados = 0
            for usuario in usuarios:
                try:
                    print(f"🟡 ENVIANDO PARA: {usuario.first_name} ({usuario.chat_id})")
                    self.application.bot.send_message(
                        chat_id=usuario.chat_id,
                        text=mensagem,
                        parse_mode="Markdown"
                    )
                    enviados += 1
                    print(f"✅ ENVIADO PARA: {usuario.first_name}")
                except Exception as e:
                    print(f"🔴 ERRO PARA {usuario.chat_id}: {e}")
            
            print(f"📊 TOTAL ENVIADO: {enviados}/{usuarios.count()}")
            return enviados > 0
            
        except Exception as e:
            print(f"🔴 ERRO CRÍTICO NO ENVIO: {e}")
            return False


class TelegramSender:
    """Classe simples para enviar mensagens via API do Telegram"""
    
    @staticmethod
    def send_message(chat_id, message, parse_mode="Markdown"):
        """Envia mensagem diretamente pela API do Telegram"""
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Mensagem enviada para {chat_id}")
                return True
            else:
                print(f"❌ Erro API Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem para {chat_id}: {e}")
            return False
    
    @staticmethod
    def send_broadcast(message):
        """Envia mensagem para todos os usuários ativos"""
        from telegram_bot.models import TelegramUser
        
        try:
            usuarios = TelegramUser.objects.filter(is_active=True)
            print(f"📢 Enviando broadcast para {usuarios.count()} usuários")
            
            if usuarios.count() == 0:
                print("❌ Nenhum usuário ativo para enviar")
                return False
            
            success_count = 0
            for usuario in usuarios:
                if TelegramSender.send_message(usuario.chat_id, message):
                    success_count += 1
                    usuario.last_alert_sent = timezone.now()
                    usuario.save(update_fields=['last_alert_sent'])
            
            print(f"✅ Broadcast: {success_count}/{usuarios.count()} enviados com sucesso")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Erro no broadcast: {e}")
            return False