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

# --- Ajuda ------------------------------------------------------------------
# Resposta a qualquer mensagem que o bot não sabe tratar (texto solto, comando
# desconhecido, figurinha, áudio...) e ao /ajuda. Uma por tipo de conta, escolhida
# em telegram_bot.services.bot_role(). {name} chega já escapado para Markdown;
# {intro} é AJUDA_NAO_ENTENDI numa mensagem não prevista e vazio no /ajuda.

AJUDA_NAO_ENTENDI = " Não entendi sua mensagem."

AJUDA_NAO_VINCULADO = (
    "Olá, {name}! 👋{intro}\n\n"
    "Eu sou o bot do *Labfito*. Para usar o bot, vincule esta conversa à sua conta: "
    "informe seu usuário do Telegram em *Dados Pessoais*, no seu perfil:\n"
    "{profile_url}\n\n"
    "Ainda não tem conta? Crie a sua em:\n"
    "{create_url}\n\n"
    "Depois envie /start para confirmar o vínculo."
)

AJUDA_COMUM = (
    "Olá, {name}! 👋{intro}\n\n"
    "Veja o que posso fazer por você:\n\n"
    "🔔 Enviar os *alertas fitossanitários* do Labfito\n"
    "/teste — ver um exemplo de alerta\n"
    "/stop — parar de receber alertas\n"
    "/start — voltar a receber alertas\n"
    "/ajuda — mostrar esta mensagem\n\n"
    "📷 Quer enviar imagens para o modelo de IA? Esse recurso é dos "
    "*contribuidores*. Solicite o status no painel:\n"
    "{solicitation_url}"
)

AJUDA_CONTRIBUIDOR = (
    "Olá, {name}! 👋{intro}\n\n"
    "Como *contribuidor*, veja o que você pode fazer por aqui:\n\n"
    "📷 *Enviar imagens* para o modelo de IA — uma ou várias de uma vez. Depois "
    "eu pergunto se são para *treinar* (1) ou *testar* (2) o modelo. Para as de "
    "treino, peço uma breve descrição de cada uma, e elas passam pela revisão de "
    "um administrador.\n\n"
    "🔔 Receber os *alertas fitossanitários*\n"
    "/teste — ver um exemplo de alerta\n"
    "/stop — parar de receber alertas\n"
    "/start — voltar a receber alertas\n"
    "/ajuda — mostrar esta mensagem"
)

AJUDA_ADMIN = (
    "Olá, {name}! 👋{intro}\n\n"
    "Como *administrador*, veja o que você pode fazer por aqui:\n\n"
    "📷 *Enviar imagens* para o modelo de IA — uma ou várias de uma vez. Depois "
    "eu pergunto se são para *treinar* (1) ou *testar* (2) o modelo. Para as de "
    "treino, peço uma breve descrição de cada uma. Elas também passam pela "
    "aprovação no painel, onde são categorizadas.\n\n"
    "🔔 Receber os *alertas fitossanitários*\n"
    "/teste — ver um exemplo de alerta\n"
    "/stop — parar de receber alertas\n"
    "/start — voltar a receber alertas\n"
    "/ajuda — mostrar esta mensagem\n\n"
    "🛠️ Os pedidos de quem quer virar contribuidor são revisados no painel:\n"
    "{solicitation_list_url}\n\n"
    "🧠 As imagens de treino são aprovadas e categorizadas em:\n"
    "{ai_model_review_url}"
)

AJUDA = {
    'unlinked': AJUDA_NAO_VINCULADO,
    'common': AJUDA_COMUM,
    'contributor': AJUDA_CONTRIBUIDOR,
    'admin': AJUDA_ADMIN,
}

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

# Primeira imagem de um lote, aceita e registrada. O arquivo só é baixado depois
# da resposta, e vai para media-ia/training/pending/ (1) ou media-ia/test/ (2).
FOTO_PERGUNTA_USO = (
    "📷 *Imagem recebida!*\n\n"
    "O que você quer fazer com ela?\n\n"
    "*1* — Treinar o modelo\n"
    "*2* — Testar o modelo\n\n"
    "Responda só com o número. Se enviar mais imagens antes de responder, a "
    "escolha vale para todas."
)

# Texto que não é 1 nem 2 enquanto há imagens esperando a escolha.
FOTO_LEMBRETE_USO = (
    "📷 Você tem *{total}* imagem(ns) aguardando.\n\n"
    "Responda *1* para treinar o modelo ou *2* para testá-lo."
)

# Resposta 2 processada. {uso} vem de FOTO_USO.
FOTO_SALVAS = (
    "✅ *{total} imagem(ns) salva(s) para {uso}.*\n\n"
    "Obrigado pela contribuição!"
)

# --- Descrição das imagens de treino ---------------------------------------
# Depois da resposta 1, cada imagem de treino precisa de uma breve descrição
# antes de ir para a aprovação no painel. Ver telegram_bot.services.save_descriptions().

# Resposta 1 com uma imagem só esperando descrição.
FOTO_PEDE_DESCRICAO = (
    "✅ *Imagem salva para treinar o modelo.*\n\n"
    "Agora me conte, em poucas palavras, o que ela mostra: qual é a planta, se "
    "ela está saudável e, se não estiver, qual doença pode ter.\n\n"
    "Exemplo: _Folha de soja com manchas, parece ferrugem asiática_"
)

# Resposta 1 com várias imagens: o bot cita cada foto com FOTO_NUMERO antes
# deste texto, para o usuário saber qual número é de qual imagem.
FOTO_PEDE_DESCRICOES = (
    "✅ *{total} imagens salvas para treinar o modelo.*\n\n"
    "Agora me conte, em poucas palavras, o que cada uma mostra: qual é a planta, "
    "se ela está saudável e, se não estiver, qual doença pode ter.\n\n"
    "Marquei cada imagem com um número. Escreva uma linha por imagem, começando "
    "pelo número:\n\n"
    "`1 - Folha de soja saudável`\n"
    "`2 - Soja com manchas, parece ferrugem asiática`\n\n"
    "Pode mandar tudo numa mensagem só ou uma por vez."
)

# Resposta citando a foto, uma por imagem do lote.
FOTO_NUMERO = "📷 Imagem *{numero}*"

# Todas as descrições recebidas.
FOTO_DESCRICOES_OK = (
    "✅ *Descrição recebida!*\n\n"
    "As imagens agora passam pela revisão de um administrador antes de entrar "
    "no treino.\n\n"
    "Obrigado pela contribuição!"
)

# Parte das descrições recebida. {faltam} é a lista de números, ex.: "2, 3".
FOTO_DESCRICOES_FALTAM = (
    "👍 Anotado. Ainda falta a descrição da(s) imagem(ns) *{faltam}*.\n\n"
    "Escreva começando pelo número, por exemplo:\n"
    "`{exemplo} - Folha de soja saudável`"
)

# Texto que não traz nenhuma descrição válida enquanto há imagens esperando.
FOTO_LEMBRETE_DESCRICAO = (
    "📷 Você tem *{total}* imagem(ns) de treino aguardando descrição "
    "(número(s) *{faltam}*).\n\n"
    "Escreva uma linha por imagem, começando pelo número, por exemplo:\n"
    "`{exemplo} - Folha de soja saudável`"
)

# Uma imagem só esperando, e o texto não serve como descrição (ex.: só um número).
FOTO_LEMBRETE_DESCRICAO_UNICA = (
    "📷 Sua imagem de treino está aguardando uma descrição.\n\n"
    "Conte em poucas palavras qual é a planta, se ela está saudável e, se não "
    "estiver, qual doença pode ter."
)

FOTO_USO = {
    'training': "treinar o modelo",
    'test': "testar o modelo",
}

# Parte das imagens do lote não pôde ser baixada ou não era imagem válida.
FOTO_FALHARAM = "⚠️ {falhas} imagem(ns) não puderam ser salvas. Envie-as novamente."

# Falha ao gravar, depois de a permissão já ter sido concedida.
FOTO_ERRO = "❌ Não foi possível salvar sua imagem. Tente novamente."

# Arquivo acima do limite de download da Bot API.
FOTO_MUITO_GRANDE = "❌ A imagem é muito grande (limite de 20 MB). Envie uma versão menor."
