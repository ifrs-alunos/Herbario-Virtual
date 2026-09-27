from django import forms
from django.contrib.auth.models import User


class UniqueEmailMixin:
    """Garante que o e-mail não esteja em uso por outra conta.

    O e-mail identifica a pessoa na recuperação de senha e no contato, então não
    pode apontar para duas contas. O `auth.User` padrão do Django não tem
    `unique=True` no campo — a garantia de banco é o índice criado em
    accounts/migrations/0003_unique_user_email.py, e esta validação existe para o
    usuário ver um erro no formulário em vez de um IntegrityError.

    O vínculo com o bot do Telegram não passa mais por aqui: quem faz esse papel
    é Profile.telegram_username.
    """

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()

        if not email:
            return email

        outros = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            outros = outros.exclude(pk=self.instance.pk)

        if outros.exists():
            raise forms.ValidationError("Já existe uma conta cadastrada com este e-mail.")

        return email
