from django import forms
from accounts.models import Solicitation

class SolicitationStatusUpdateForm(forms.ModelForm):
    """Essa classe é utilizada para negar ou aceitar uma solicitação, isto é, mudar o seu status"""

    class Meta:
        model = Solicitation
        fields = ['status']