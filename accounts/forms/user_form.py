from django import forms
from django.forms import widgets

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 

class UserForm(UserCreationForm):
    email = forms.EmailField(label="E-mail")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        labels = {
            'username': 'Nome de usuário',
        }     