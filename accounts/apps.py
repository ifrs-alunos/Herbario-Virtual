from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'accounts'
    
    def ready(self):
        # Importe os signals apenas depois que o Django estiver totalmente carregado
        import accounts.signals