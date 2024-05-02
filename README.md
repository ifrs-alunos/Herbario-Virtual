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

3. Edite o arquivo `.env` como necessário
   - O arquivo `.env` é um arquivo de configuração usado no Docker Compose, onde você pode definir variáveis de ambiente para o projeto
   - Por padrão, o arquivo `.env` já está configurado para rodar o projeto em ambiente de desenvolvimento
   - Você pode alterar as variáveis de ambiente conforme necessário

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

5. Execute o comando `docker-compose up` na raiz do projeto
   - Isso vai criar os containers do projeto e instalar as dependências, bem como subir o banco de dados

6. Acesse o projeto em http://localhost:8000 

7. Para executar comandos de gerenciamento do Django, execute o comando `docker-compose run web python manage.py <comando>`
   #### Exemplos: 
   - Criar super usuário `docker-compose run labfito python manage.py createsuperuser`
   - Criar migrações `docker-compose run labfito python manage.py makemigrations`
   - Aplicar migrações `docker-compose run labfito python manage.py migrate`