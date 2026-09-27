# Herbário Virtual
Herbário Virtual de plantas daninhas

OBS: SE RODAR ESSE PROJETO PELA PRIMERA VEZ, CRIE UM ARQUIVO DENTRO DA PASTA 'config' CHAMADO 'local_settings.py' E COLOQUE
AS CONFIGURAÇÕES DO AMBIENTE LOCAL, INCLUINDO, OBRIGATORIAMENTE, OS DADOS LOCAIS DO BANCO DE DADOS. DO CONTRÁRIO, UM ERRO
SERÁ DISPARADO.

### Ambiente de desenvolvimento

#### Docker
Para executar o projeto em um ambiente de desenvolvimento, é necessário ter o Docker e Docker Compose instalados. 

Siga as instruções do site oficial: https://docs.docker.com/get-docker/

#### Executando o projeto
1. Clone o repositório

2. Abra a pasta do projeto no seu editor de código de preferência

3. Crie o arquivo `.env` a partir do modelo: `cp .env.example .env`
   - O arquivo `.env` é um arquivo de configuração usado no Docker Compose, onde você pode definir variáveis de ambiente para o projeto
   - O `.env` **não é versionado** (está no `.gitignore`): cada ambiente tem o seu, com as próprias senhas e tokens
   - Veja a seção [Variáveis de ambiente](#variáveis-de-ambiente) para o que cada variável faz, e a seção [Bot do Telegram](#bot-do-telegram) para configurar o bot

4. Edite o arquivo `local_settings.py` dentro da pasta `config` com as configurações do ambiente local
   - O arquivo `local_settings.py` é um arquivo de configuração do Django, onde você pode definir as configurações do ambiente local
   - Você pode copiar o arquivo `local_settings.py.example` e renomeá-lo para `local_settings.py` para facilitar
   - Você pode definir outras configurações do ambiente local conforme necessário
   - A configuração do banco de dados pode ser realizada da seguinte forma:
   
    ```py
   DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("POSTGRES_DB"),
        'USER': os.environ.get("POSTGRES_USER"),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD"),
        'HOST': "db",
        'PORT': '5432'
        }
    }
    ```

5. Execute o comando `docker compose up` na raiz do projeto
   - Isso vai criar os containers do projeto e instalar as dependências, bem como subir o banco de dados
   - Sobem três serviços: `labfito` (o site), `bot` (o bot do Telegram) e `db` (PostgreSQL)

6. Acesse o projeto em http://localhost:8000 

7. Para executar comandos de gerenciamento do Django, execute o comando `docker compose run labfito python manage.py <comando>`
   #### Exemplos: 
   - Criar super usuário `docker compose run labfito python manage.py createsuperuser`
   - Criar migrações `docker compose run labfito python manage.py makemigrations`
   - Aplicar migrações `docker compose run labfito python manage.py migrate`
   - Rodar os testes `docker compose run labfito python manage.py test accounts dashboard disease herbarium telegram_bot`

#### Ajustes só da sua máquina (outra porta, por exemplo)
Se a porta 8000 já estiver em uso, **não altere o `docker-compose.yaml`**, que é o mesmo de produção. Crie um arquivo
`docker-compose.override.yml` na raiz do projeto. O Docker Compose lê esse arquivo automaticamente, e ele está no
`.gitignore`:

```yaml
services:
  labfito:
    ports: !override
      - "8001:8000"
```

### Variáveis de ambiente

Todas ficam no `.env` de cada ambiente. O modelo com os nomes está em `.env.example`.

| Variável | Para que serve |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Banco de dados |
| `SECRET_KEY` | Chave secreta do Django |
| `SITE_URL` | Endereço público do site, usado nas mensagens do bot. Padrão: `https://labfito.vacaria.ifrs.edu.br` |
| `TELEGRAM_BOT_USERNAME` | Nome do bot do Telegram, **sem** o `@`. Padrão: `labfito_vacaria_bot` (produção) |
| `TELEGRAM_BOT_TOKEN` | Token do bot do Telegram. **Sem valor padrão**: sem ele, o bot não funciona |

Depois de alterar o `.env`, recrie os containers com `docker compose up -d`. Um `docker compose restart` **não** relê o `.env`.

### Bot do Telegram

O sistema envia alertas e recebe imagens por um bot do Telegram. **Cada ambiente usa o seu próprio bot**, para que
testes nunca cheguem a usuários reais:

| Ambiente | Bot |
|---|---|
| Produção | [@labfito_vacaria_bot](https://t.me/labfito_vacaria_bot) |
| Desenvolvimento | `@labfito_teste_bot`, ou um bot seu criado no [@BotFather](https://t.me/BotFather) |

Regras:

- **O token nunca vai para o código nem para o repositório**, que é público. Ele fica só no `.env` de cada ambiente.
  Quem tiver um token exposto por engano deve revogá-lo no @BotFather (`/revoke`) e gerar outro.
- **Nunca use o token de produção no seu `.env` local.** O Telegram só permite uma instância lendo mensagens por bot.
  Com o mesmo token nos dois lugares, o bot local e o de produção se derrubam alternadamente (erro `Conflict` no log).
- Se `TELEGRAM_BOT_TOKEN` estiver vazio, o serviço `bot` não sobe e nenhum alerta sai pelo Telegram. O site continua
  funcionando normalmente.

No `.env` de desenvolvimento:

```
TELEGRAM_BOT_USERNAME=labfito_teste_bot
TELEGRAM_BOT_TOKEN=<token do bot de teste>
```

### Produção

O repositório não tem deploy automático. Enviar código ao GitHub **não altera** o servidor: a atualização é feita no
próprio servidor.

1. Faça um dump do banco antes de qualquer atualização que traga migrações.
2. Atualize o código: `git pull`.
3. Confira o `.env` do servidor. Ele deve ter `TELEGRAM_BOT_USERNAME=labfito_vacaria_bot` e o `TELEGRAM_BOT_TOKEN`
   desse bot. O token é guardado pela equipe responsável e não fica no repositório.
4. Recrie os containers: `docker compose up -d --build`.
5. Aplique as migrações: `docker compose exec labfito python manage.py migrate`.
