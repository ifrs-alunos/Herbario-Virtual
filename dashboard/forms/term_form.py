from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Profile


class TermForm(forms.Form):
	password = forms.CharField(label='Confirme sua senha', max_length=200, widget=forms.PasswordInput)


