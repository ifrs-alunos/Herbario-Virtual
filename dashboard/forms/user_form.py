from django import forms
from django.forms import widgets

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 

class UserForm(UserCreationForm):
    email = forms.EmailField(label="E-mail")

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        
        self.fields['password1'].help_text = "Mínimo 8 caracteres. Não use dados pessoais, senhas comuns ou somente números."
        self.fields['username'].help_text = "Credencial utilizada para login. Use letras, números e os símbolos @/./+/-/_ apenas."
        
    # password1 = forms.CharField(label="Senha", help_text="Mínimo 8 caracteres. É proibido somente números, dados pessoais ou senhas comuns")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        labels = {
            'username': 'Nome de usuário',
        }     