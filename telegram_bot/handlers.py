import logging
import asyncio
import threading
import time
import sys
from asgiref.sync import sync_to_async
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
            # chat_id -> media_group_id da última recusa. Ver _album_ja_respondido.
            cls._instance._ultimo_album_recusado = {}
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
                # Precisa vir ANTES do handler geral: dentro de um mesmo grupo,
                # apenas o primeiro handler que casa com a mensagem é executado
                self.application.add_handler(
                    MessageHandler(filters.PHOTO | filters.Document.IMAGE, self._handle_photo)
                )
                # Texto puro de quem ainda não vinculou a conta. O ~filters.COMMAND
                # impede que um comando digitado errado caia aqui.
                self.application.add_handler(
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
                )
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

    def _album_ja_respondido(self, chat_id, media_group_id):
        """Evita repetir a mesma recusa uma vez por foto de um álbum.

        Um álbum chega como vários updates independentes, todos com o mesmo
        media_group_id. Sem isto, recusar 8 fotos manda 8 mensagens idênticas.

        A memória é do processo e guarda só o último álbum recusado de cada chat:
        se o bot reiniciar, o pior que acontece é uma recusa repetida.
        """

        if not media_group_id:
            return False

        if self._ultimo_album_recusado.get(chat_id) == media_group_id:
            return True

        self._ultimo_album_recusado[chat_id] = media_group_id

        return False

    async def _handle_photo(self, update, context):
        """Handler para imagens (foto comprimida ou enviada como arquivo)"""
        try:
            from telegram_bot import messages
            from telegram_bot.services import (
                MAX_TELEGRAM_FILE_SIZE, PhotoPermission, photo_permission,
                save_incoming_photo, site_url,
            )

            message = update.message
            user = update.effective_user
            chat_id = update.effective_chat.id

            print(f"🖼️ IMAGEM RECEBIDA DE: {user.first_name} ({chat_id})")

            # A permissão vem ANTES do download: não faz sentido baixar até 20 MB
            # de uma imagem que vai ser descartada. Só strings saem daqui — tocar
            # no ORM em contexto async levanta SynchronousOnlyOperation.
            permissao = await sync_to_async(photo_permission)(chat_id)

            if permissao.status != PhotoPermission.ALLOWED:
                if self._album_ja_respondido(chat_id, message.media_group_id):
                    print(f"🔇 RECUSA JÁ ENVIADA PARA O ÁLBUM: {message.media_group_id}")
                    return

                if permissao.status == PhotoPermission.NOT_LINKED:
                    print(f"⛔ IMAGEM DE CHAT NÃO VINCULADO: {chat_id}")
                    resposta = messages.FOTO_PRECISA_VINCULAR.format(
                        profile_url=site_url('dashboard:profile'),
                        create_url=site_url('dashboard:create'),
                    )
                else:
                    print(f"⛔ IMAGEM DE USUÁRIO COMUM: {chat_id}")
                    resposta = messages.FOTO_PRECISA_SER_CONTRIBUIDOR.format(
                        profile_name=permissao.profile_name,
                        solicitation_url=site_url('dashboard:solicitation'),
                    )

                await message.reply_text(resposta, parse_mode="Markdown")
                return

            if message.photo:
                # A última posição é sempre a maior resolução disponível
                media = message.photo[-1]
                filename = f"{media.file_unique_id}.jpg"
                source = 'photo'
            else:
                media = message.document
                filename = media.file_name or f"{media.file_unique_id}.jpg"
                source = 'document'

            if media.file_size and media.file_size > MAX_TELEGRAM_FILE_SIZE:
                print(f"🔴 ARQUIVO MUITO GRANDE: {media.file_size} bytes")
                await message.reply_text(messages.FOTO_MUITO_GRANDE)
                return

            print(f"⬇️ BAIXANDO ARQUIVO: {filename}")
            telegram_file = await context.bot.get_file(media.file_id)
            image_bytes = bytes(await telegram_file.download_as_bytearray())

            photo = await sync_to_async(save_incoming_photo)(
                chat_id=chat_id,
                image_bytes=image_bytes,
                filename=filename,
                username=user.username or "",
                first_name=user.first_name or "",
                file_id=media.file_id,
                file_unique_id=media.file_unique_id,
                file_size=media.file_size,
                caption=message.caption or "",
                telegram_message_id=message.message_id,
                media_group_id=message.media_group_id or "",
                source=source,
            )

            print(f"✅ IMAGEM SALVA: #{photo.pk} em {photo.image.name}")

            await message.reply_text(
                messages.FOTO_RECEBIDA.format(
                    photo_id=photo.pk,
                    recebida_em=f"{timezone.localtime(photo.received_at):%d/%m/%Y %H:%M}",
                ),
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"🔴 ERRO AO RECEBER IMAGEM: {e}")
            import traceback
            traceback.print_exc()
            from telegram_bot import messages
            await update.message.reply_text(messages.FOTO_ERRO)

    async def _handle_start(self, update, context):
        """Handler para /start — resolve o vínculo pelo @username do Telegram"""
        try:
            print(f"🎯 /start RECEBIDO DE: {update.effective_user.first_name}")

            from telegram_bot import messages
            from telegram_bot.services import LinkStatus, link_by_telegram_username, site_url

            chat_id = update.effective_chat.id
            user = update.effective_user

            resultado = await sync_to_async(link_by_telegram_username)(
                chat_id=chat_id,
                username=user.username or "",
                first_name=user.first_name or ""
            )

            # Só strings daqui para baixo: tocar no ORM em contexto async
            # levanta SynchronousOnlyOperation. Ver Docs/2026-08-11-plano-correcao-vinculo-async.md
            if resultado.status == LinkStatus.OK:
                print(f"✅ VINCULADO: {chat_id} -> {resultado.username}")
                resposta = messages.VINCULO_OK.format(
                    profile_name=resultado.profile_name,
                    username=resultado.username,
                )
            elif resultado.status == LinkStatus.ALREADY_LINKED:
                print(f"✅ CHAT JÁ VINCULADO: {chat_id}")
                resposta = messages.JA_VINCULADO.format(username=resultado.username)
            elif resultado.status == LinkStatus.TAKEN:
                print(f"⚠️ @ JÁ VINCULADO A OUTRO CHAT: {resultado.telegram_username}")
                resposta = messages.USERNAME_JA_USADO.format(
                    username=resultado.telegram_username
                )
            elif resultado.status == LinkStatus.NO_USERNAME:
                print(f"⚠️ CONTA DO TELEGRAM SEM @: {chat_id}")
                resposta = messages.SEM_USERNAME.format(first_name=user.first_name or "")
            else:
                print(f"📝 @ SEM PERFIL CORRESPONDENTE: {resultado.telegram_username}")
                resposta = messages.USERNAME_NAO_ENCONTRADO.format(
                    username=resultado.telegram_username,
                    profile_url=site_url('dashboard:profile'),
                    create_url=site_url('dashboard:create'),
                )

            await update.message.reply_text(resposta, parse_mode="Markdown")

        except Exception as e:
            print(f"🔴 ERRO NO /start: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text("❌ Erro no cadastro. Tente novamente.")

    async def _handle_text(self, update, context):
        """Handler para texto puro — o vínculo não se faz por aqui, só orienta"""
        try:
            from telegram_bot import messages
            from telegram_bot.services import get_link_state

            chat_id = update.effective_chat.id
            texto = update.message.text

            estado = await sync_to_async(get_link_state)(chat_id)

            if estado == 'linked':
                # Conversa vinculada: nada a fazer com texto solto, só registra.
                print(f"📨 MENSAGEM DE CHAT VINCULADO {chat_id}: '{texto}'")
                return

            await update.message.reply_text(
                messages.PRECISA_VINCULAR, parse_mode="Markdown"
            )

        except Exception as e:
            print(f"🔴 ERRO NO HANDLER DE TEXTO: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text("❌ Erro ao processar sua mensagem. Tente novamente.")

    async def _handle_stop(self, update, context):
        """Handler para /stop — para os alertas, mas mantém o vínculo"""
        try:
            print(f"🎯 /stop RECEBIDO DE: {update.effective_user.first_name}")

            from telegram_bot import messages
            from telegram_bot.models import TelegramUser

            chat_id = update.effective_chat.id
            success = await sync_to_async(TelegramUser.unsubscribe)(chat_id)

            if success:
                await update.message.reply_text(
                    messages.ALERTAS_DESATIVADOS, parse_mode="Markdown"
                )
                print(f"✅ ALERTAS DESATIVADOS: {chat_id}")
            else:
                await update.message.reply_text(messages.NAO_CADASTRADO)

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
