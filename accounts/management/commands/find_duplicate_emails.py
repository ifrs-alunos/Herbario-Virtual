from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import Upper


class Command(BaseCommand):
    help = (
        "Lista contas que compartilham o mesmo e-mail (ignorando maiúsculas). "
        "Rode antes de aplicar a migração que torna o e-mail único. "
        "Sai com código 1 se houver duplicatas."
    )

    def handle(self, *args, **options):
        duplicados = (
            User.objects.exclude(email='')
            .annotate(chave=Upper('email'))
            .values('chave')
            .annotate(total=Count('id'))
            .filter(total__gt=1)
            .order_by('-total')
        )

        if not duplicados:
            self.stdout.write(self.style.SUCCESS("Nenhum e-mail duplicado encontrado."))
            return

        self.stdout.write(
            self.style.ERROR("{} e-mail(s) em uso por mais de uma conta:".format(len(duplicados)))
        )

        for grupo in duplicados:
            self.stdout.write("\n  {} — {} contas:".format(grupo['chave'], grupo['total']))
            contas = User.objects.filter(email__iexact=grupo['chave']).order_by('id')
            for conta in contas:
                self.stdout.write(
                    "    id={} username={} email={} último login={}".format(
                        conta.id, conta.username, conta.email, conta.last_login
                    )
                )

        self.stdout.write(
            self.style.WARNING(
                "\nResolva manualmente em /admin/auth/user/ antes de migrar: "
                "cada conta precisa de um e-mail próprio."
            )
        )

        # Código de saída != 0 para poder travar um deploy automatizado.
        raise SystemExit(1)
