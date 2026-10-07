from django import forms

from ..models import Profile
from ..models.profile import TELEGRAM_USERNAME_RE, normalize_telegram_username


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['user']

    def clean_telegram_username(self):
        """Normaliza o @ do Telegram e garante que só um perfil o reivindique.

        A checagem de duplicidade repete o `unique` do banco de propósito, pelo
        mesmo motivo do UniqueEmailMixin: o usuário vê um erro no formulário em
        vez de um IntegrityError.
        """

        username = normalize_telegram_username(self.cleaned_data.get('telegram_username'))

        if username is None:
            return None

        if not TELEGRAM_USERNAME_RE.match(username):
            raise forms.ValidationError(
                "Nome de usuário do Telegram inválido. Ele tem de 5 a 32 caracteres "
                "e usa apenas letras, números e _ (underline)."
            )

        outros = Profile.objects.filter(telegram_username=username)
        if self.instance and self.instance.pk:
            outros = outros.exclude(pk=self.instance.pk)

        if outros.exists():
            raise forms.ValidationError(
                "Este usuário do Telegram já está vinculado a outra conta do Labfito."
            )

        return username
