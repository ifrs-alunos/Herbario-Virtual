import logging
import asyncio
import threading
import time
import sys
from asgiref.sync import sync_to_async
from django.conf import settings

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
                self.application.add_handler(CommandHandler(["ajuda", "help"], self._handle_help))
                # Precisa vir ANTES do handler geral: dentro de um mesmo grupo,
                # apenas o primeiro handler que casa com a mensagem é executado
                self.application.add_handler(
                    MessageHandler(filters.PHOTO | filters.Document.IMAGE, self._handle_photo)
                )
                # Texto puro: resposta 1/2 às imagens pendentes, descrição das
                # imagens de treino ou, fora disso, a ajuda. O ~filters.COMMAND deixa comando desconhecido para o
                # handler geral, que também responde com a ajuda.
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
        """Tudo que nenhum outro handler tratou: comando desconhecido, figurinha,
        áudio, vídeo, localização... Responde com a ajuda do tipo de usuário."""
        try:
            message = update.message

            # Edições de mensagem e outros updates sem `message` não têm a quem responder
            if message is None:
                return

            print(f"📨 MENSAGEM NÃO PREVISTA DE {update.effective_chat.id}: '{message.text or '[sem texto]'}'")

            # Um álbum de vídeos, por exemplo, chega como vários updates: uma ajuda só
            if self._album_ja_respondido(update.effective_chat.id, message.media_group_id):
                return

            await self._responder_ajuda(update)

        except Exception as e:
            print(f"🔴 ERRO NO HANDLER GERAL: {e}")
            import traceback
            traceback.print_exc()

    async def _handle_help(self, update, context):
        """Handler para /ajuda e /help"""
        try:
            await self._responder_ajuda(update, nao_entendi=False)
        except Exception as e:
            print(f"🔴 ERRO NO /ajuda: {e}")
            await update.message.reply_text("❌ Erro ao mostrar a ajuda.")

    async def _responder_ajuda(self, update, nao_entendi=True):
        """Chama o usuário pelo nome e explica o que o bot faz para o tipo de conta dele"""

        from telegram.helpers import escape_markdown

        from telegram_bot import messages
        from telegram_bot.services import bot_role, site_url

        papel = await sync_to_async(bot_role)(update.effective_chat.id)

        # Quem não vinculou ainda não tem nome no Labfito: usa o do Telegram.
        # Escapado porque o nome vem do usuário e um `_` solto quebra o Markdown.
        nome = escape_markdown(papel.name or update.effective_user.first_name or "", version=1)

        texto = messages.AJUDA[papel.role].format(
            name=nome,
            intro=messages.AJUDA_NAO_ENTENDI if nao_entendi else "",
            profile_url=site_url('dashboard:profile'),
            create_url=site_url('dashboard:create'),
            solicitation_url=site_url('dashboard:solicitation'),
            solicitation_list_url=site_url('dashboard:solicitation_list'),
            ai_model_review_url=site_url('dashboard:ai_model_review'),
        )

        print(f"💡 AJUDA ({papel.role}) PARA {update.effective_chat.id}")

        await update.message.reply_text(texto, parse_mode="Markdown")

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
                register_pending_photo, site_url,
            )

            message = update.message
            user = update.effective_user
            chat_id = update.effective_chat.id

            print(f"🖼️ IMAGEM RECEBIDA DE: {user.first_name} ({chat_id})")

            # A permissão vem ANTES de registrar: imagem de quem não pode enviar
            # não deixa rastro no banco nem em media-ia/. Só strings saem daqui — tocar
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
                file_name = ""
                source = 'photo'
            else:
                media = message.document
                file_name = media.file_name or ""
                source = 'document'

            if media.file_size and media.file_size > MAX_TELEGRAM_FILE_SIZE:
                print(f"🔴 ARQUIVO MUITO GRANDE: {media.file_size} bytes")
                await message.reply_text(messages.FOTO_MUITO_GRANDE)
                return

            # Só registra: o download fica para quando o usuário disser se a
            # imagem é para treinar ou testar, e aí vai direto para a pasta certa.
            photo, perguntar = await sync_to_async(register_pending_photo)(
                chat_id=chat_id,
                username=user.username or "",
                first_name=user.first_name or "",
                file_id=media.file_id,
                file_unique_id=media.file_unique_id,
                file_size=media.file_size,
                file_name=file_name,
                caption=message.caption or "",
                telegram_message_id=message.message_id,
                media_group_id=message.media_group_id or "",
                source=source,
            )

            print(f"🕓 IMAGEM #{photo.pk} AGUARDANDO ESCOLHA DE USO")

            if perguntar:
                await message.reply_text(messages.FOTO_PERGUNTA_USO, parse_mode="Markdown")

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
        """Handler para texto puro: a resposta 1/2 às imagens pendentes, a
        descrição das imagens de treino ou, fora disso, a ajuda. O vínculo não
        se faz por aqui."""
        try:
            from telegram_bot.services import (
                get_link_state, pending_description_numbers, pending_photos,
            )

            chat_id = update.effective_chat.id
            texto = update.message.text

            estado = await sync_to_async(get_link_state)(chat_id)

            if estado == 'linked':
                # A pergunta 1/2 vem primeiro: imagens novas chegando no meio das
                # descrições ainda não sabem se são de treino.
                pendentes = await sync_to_async(pending_photos)(chat_id)

                if pendentes:
                    await self._classificar_fotos(update, context, pendentes, texto)
                    return

                if await sync_to_async(pending_description_numbers)(chat_id):
                    await self._registrar_descricoes(update, texto)
                    return

            print(f"📨 TEXTO NÃO PREVISTO DE {chat_id}: '{texto}'")
            await self._responder_ajuda(update)

        except Exception as e:
            print(f"🔴 ERRO NO HANDLER DE TEXTO: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text("❌ Erro ao processar sua mensagem. Tente novamente.")

    async def _classificar_fotos(self, update, context, pendentes, texto):
        """Trata a resposta 1 (treinar) ou 2 (testar) às imagens pendentes do chat.

        Baixa cada imagem e a grava em media-ia/training/pending/ ou media-ia/test/. A
        que falhar é descartada e o usuário é avisado para reenviá-la. Para as de
        treino, pede em seguida a descrição de cada uma.
        """

        from telegram_bot import messages
        from telegram_bot.models import TelegramPhoto
        from telegram_bot.services import (
            PURPOSE_BY_ANSWER, discard_pending_photo, store_photo_file,
        )

        chat_id = update.effective_chat.id

        purpose = PURPOSE_BY_ANSWER.get(texto.strip())

        if purpose is None:
            await update.message.reply_text(
                messages.FOTO_LEMBRETE_USO.format(total=len(pendentes)),
                parse_mode="Markdown"
            )
            return

        salvas = 0

        for pendente in pendentes:
            try:
                telegram_file = await context.bot.get_file(pendente.file_id)
                image_bytes = bytes(await telegram_file.download_as_bytearray())
                await sync_to_async(store_photo_file)(pendente.id, image_bytes, purpose)
                salvas += 1
            except Exception as e:
                print(f"🔴 FALHA AO GRAVAR IMAGEM #{pendente.id}: {e}")
                await sync_to_async(discard_pending_photo)(pendente.id)

        print(f"✅ {salvas}/{len(pendentes)} IMAGENS GRAVADAS EM {purpose}")

        falhas = len(pendentes) - salvas

        if purpose == TelegramPhoto.PURPOSE_TRAINING and salvas:
            await self._pedir_descricoes(update, context, chat_id, falhas)
            return

        partes = []
        if salvas:
            partes.append(messages.FOTO_SALVAS.format(total=salvas, uso=messages.FOTO_USO[purpose]))
        if falhas:
            partes.append(messages.FOTO_FALHARAM.format(falhas=falhas))

        await update.message.reply_text("\n\n".join(partes), parse_mode="Markdown")

    async def _pedir_descricoes(self, update, context, chat_id, falhas=0):
        """Pede a descrição das imagens de treino que acabaram de ser gravadas.

        Com mais de uma imagem esperando, cita cada foto com o número dela antes
        de explicar o formato "1 - texto": sem isso o usuário não sabe qual
        número corresponde a qual imagem de um álbum.
        """

        from telegram_bot import messages
        from telegram_bot.services import request_descriptions

        pedidos = await sync_to_async(request_descriptions)(chat_id)

        if len(pedidos) > 1:
            for pedido in pedidos:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=messages.FOTO_NUMERO.format(numero=pedido.number),
                    parse_mode="Markdown",
                    reply_to_message_id=pedido.telegram_message_id,
                    # A foto pode ter sido apagada pelo usuário: manda assim mesmo
                    allow_sending_without_reply=True,
                )
            texto = messages.FOTO_PEDE_DESCRICOES.format(total=len(pedidos))
        else:
            texto = messages.FOTO_PEDE_DESCRICAO

        if falhas:
            texto = "{}\n\n{}".format(texto, messages.FOTO_FALHARAM.format(falhas=falhas))

        await update.message.reply_text(texto, parse_mode="Markdown")

    async def _registrar_descricoes(self, update, texto):
        """Grava as descrições das imagens de treino e diz o que ainda falta"""

        from telegram_bot import messages
        from telegram_bot.services import save_descriptions

        chat_id = update.effective_chat.id

        resultado = await sync_to_async(save_descriptions)(chat_id, texto)

        print(f"📝 DESCRIÇÕES DE {chat_id}: gravadas {resultado.saved}, faltam {resultado.missing}")

        faltam = ", ".join(str(n) for n in resultado.missing)
        exemplo = resultado.missing[0] if resultado.missing else 1

        if not resultado.missing:
            resposta = messages.FOTO_DESCRICOES_OK
        elif resultado.saved:
            resposta = messages.FOTO_DESCRICOES_FALTAM.format(faltam=faltam, exemplo=exemplo)
        elif len(resultado.missing) == 1:
            resposta = messages.FOTO_LEMBRETE_DESCRICAO_UNICA
        else:
            resposta = messages.FOTO_LEMBRETE_DESCRICAO.format(
                total=len(resultado.missing), faltam=faltam, exemplo=exemplo,
            )

        await update.message.reply_text(resposta, parse_mode="Markdown")

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
