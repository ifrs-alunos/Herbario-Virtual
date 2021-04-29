from django import forms
from django.forms import widgets
from accounts.models import Solicitation
from django.contrib.auth import get_user_model

class SolicitationForm(forms.ModelForm): 
    user = forms.ModelChoiceField(get_user_model().objects.all(), disabled=True, widget=forms.HiddenInput)
    class Meta:
        model = Solicitation
        fields = ['user', 'message']