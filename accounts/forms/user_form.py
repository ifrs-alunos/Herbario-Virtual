from django import forms
from django.forms import widgets
from django.forms.fields import CharField
from ..models import User

class UserForm(forms.ModelForm):
    class Meta:
        model = User # Indica o modelo a ser usado
        fields = '__all__' # Indica que todos os campos do modelo serão utilizados no formulário

        # widgets = {
        #     "password": CharField(forms.PasswordInput)
        # }