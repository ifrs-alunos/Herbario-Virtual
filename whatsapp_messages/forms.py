from django import forms
from django.core.exceptions import ValidationError
from disease.models import Disease

class AlertPreferencesForm(forms.Form):
    whatsapp_enabled = forms.BooleanField(
        required=False,
        label="Receber alertas por WhatsApp"
    )
    telegram_enabled = forms.BooleanField(
        required=False,
        label="Receber alertas por Telegram"
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Número de WhatsApp"
    )
    diseases = forms.ModelMultipleChoiceField(
        queryset=Disease.objects.all(),
        required=False,
        label="Doenças para alertas",
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            self.fields['whatsapp_enabled'].initial = getattr(profile, 'whatsapp_enabled', False)
            self.fields['telegram_enabled'].initial = getattr(profile, 'telegram_enabled', False)
            self.fields['phone'].initial = getattr(profile, 'phone', '')
            self.fields['diseases'].initial = getattr(profile, 'alerts_for_diseases', Disease.objects.none())

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if self.cleaned_data.get('whatsapp_enabled') and not phone:
            raise ValidationError("Número de telefone é obrigatório para alertas por WhatsApp")
        return phone