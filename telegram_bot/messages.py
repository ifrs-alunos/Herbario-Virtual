"""Textos que o bot envia, em um lugar só.

Ficam separados dos handlers para poderem ser conferidos nos testes sem depender
da API do Telegram, e para que ajustar a redação não exija mexer na lógica.

Todos usam parse_mode="Markdown". Cuidado ao editar: `_`, `*` e `[` são
significativos para o Telegram e um par desbalanceado faz a API rejeitar o envio.
"""

# /start de quem não tem @username definido na conta do Telegram.
# Sem @ não há como o Labfito reconhecer quem está falando.
SEM_USERNAME = (
    "👋 Olá, {first_name}!\n\n"
    "Sua conta do Telegram ainda não tem um *nome de usuário* (@).\n\n"
    "É por ele que o *Labfito* reconhece você, então defina um em:\n"
    "*Configurações → Editar perfil → Nome de usuário*\n\n"
    "Depois informe esse mesmo @ no seu perfil do Labfito e envie /start de novo."
)

# /start de um @ que nenhum perfil do Labfito declarou.
USERNAME_NAO_ENCONTRADO = (
    "❌ Nenhuma conta do Labfito informou o usuário *@{username}*.\n\n"
    "Para receber os alertas, entre na sua conta do Labfito, abra *Dados "
    "Pessoais* no seu perfil e preencha o campo *Usuário do Telegram* com "
    "`{username}`:\n"
    "{profile_url}\n\n"
    "Assim que salvar, o vínculo é feito automaticamente — você nem precisa "
    "voltar aqui.\n\n"
    "Ainda não tem conta? Crie a sua em:\n"
    "{create_url}"
)

# O @ existe em um perfil, mas outra conversa do Telegram já o reivindicou.
USERNAME_JA_USADO = (
    "⚠️ O usuário *@{username}* já está vinculado a *outra* conversa do Telegram.\n\n"
    "Se foi você quem vinculou em outra conta do Telegram, use aquela conversa "
    "normalmente. Se não foi, peça a um administrador do Labfito para desfazer "
    "o vínculo."
)

# Vínculo concluído — no /start ou logo depois de o usuário salvar o @ no site.
VINCULO_OK = (
    "✅ *Conta vinculada com sucesso!*\n\n"
    "Olá, {profile_name}! Esta conversa está ligada à conta *{username}* do Labfito.\n\n"
    "A partir de agora você recebe os alertas fitossanitários por aqui.\n\n"
    "/teste — ver um exemplo de alerta\n"
    "/stop — parar de receber alertas"
)

# /start de uma conversa que já está vinculada.
JA_VINCULADO = (
    "✅ *Esta conversa já está vinculada* à conta *{username}*.\n\n"
    "Você está recebendo os alertas do Labfito por aqui.\n\n"
    "/teste — ver um exemplo de alerta\n"
    "/stop — parar de receber alertas"
)

# Texto solto de uma conversa não vinculada.
PRECISA_VINCULAR = (
    "Não entendi. 🙂\n\n"
    "Para receber os alertas do Labfito é preciso vincular esta conversa à sua "
    "conta do sistema — informe seu usuário do Telegram no perfil do Labfito.\n\n"
    "Envie /start para verificar."
)

# /stop de uma conversa vinculada — o vínculo permanece, só os alertas param.
ALERTAS_DESATIVADOS = (
    "🔕 *Alertas desativados.*\n\n"
    "Sua conta continua vinculada — envie /start para voltar a receber."
)

# /stop de quem nunca se cadastrou.
NAO_CADASTRADO = "❌ Você não estava cadastrado."


# --- Envio de imagens -------------------------------------------------------
# Quem pode enviar é decidido em telegram_bot.services.photo_permission().

# Imagem de um chat que não está ligado a nenhuma conta do Labfito.
FOTO_PRECISA_VINCULAR = (
    "📷 Recebi sua imagem, mas *não posso guardá-la ainda*.\n\n"
    "Esta conversa não está vinculada a nenhuma conta do Labfito, e só "
    "contribuidores cadastrados podem enviar imagens.\n\n"
    "Para vincular, informe seu usuário do Telegram em *Dados Pessoais*, no seu "
    "perfil:\n"
    "{profile_url}\n\n"
    "Ainda não tem conta? Crie a sua em:\n"
    "{create_url}\n\n"
    "Depois envie /start para confirmar o vínculo."
)

# Imagem de uma conta vinculada que ainda é usuário comum. É o caso central da
# regra: a imagem não é salva, e o texto diz o que fazer para poder enviar.
FOTO_PRECISA_SER_CONTRIBUIDOR = (
    "📷 Recebi sua imagem, {profile_name}, mas *ela não foi salva*.\n\n"
    "O envio de imagens é exclusivo dos *contribuidores* do Labfito, e sua conta "
    "consta como usuário comum.\n\n"
    "Para poder enviar, solicite o status de contribuidor no painel:\n"
    "{solicitation_url}\n\n"
    "Assim que um administrador aprovar seu pedido, é só reenviar a imagem por aqui."
)

# Imagem aceita e gravada.
FOTO_RECEBIDA = (
    "✅ *Imagem recebida com sucesso!*\n\n"
    "🆔 Registro: #{photo_id}\n"
    "📅 Recebida em: {recebida_em}\n\n"
    "Em breve novas funcionalidades usarão esta imagem."
)

# Falha ao gravar, depois de a permissão já ter sido concedida.
FOTO_ERRO = "❌ Não foi possível salvar sua imagem. Tente novamente."

# Arquivo acima do limite de download da Bot API.
FOTO_MUITO_GRANDE = "❌ A imagem é muito grande (limite de 20 MB). Envie uma versão menor."
