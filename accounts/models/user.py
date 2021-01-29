from django.db import models

class User(models.Model):
    name = models.CharField(verbose_name='Nome Completo', max_length=150)
    email = models.EmailField(verbose_name='E-mail')
    username = models.CharField(verbose_name='Nome de Usuário', max_length=25, unique=True)
    password = models.CharField(verbose_name='Senha', max_length=100)

    # PARA FAZER: usuário comum terá acesso a uma interface para cadastrar novas plantas, enquanto usuários administradores
    # terão acesso a um painel de controle para ver solicitações de novos cadastramento, bem como excluir e adicionar qualquer conteúdos

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['name']
