from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Importe os signals apenas depois que o Django estiver totalmente carregado
        import accounts.signals

        from accounts.permissions import ensure_default_groups

        # Sem `sender`: o receiver roda no post_migrate de cada app, e não só no
        # de accounts. As permissões de herbarium/disease são criadas no
        # post_migrate desses apps — restringindo ao sender, a primeira passada
        # não as encontrava e os grupos ficavam incompletos até o `migrate`
        # seguinte. A função é idempotente, então repetir não custa nada.
        post_migrate.connect(ensure_default_groups, dispatch_uid='accounts.ensure_default_groups')
