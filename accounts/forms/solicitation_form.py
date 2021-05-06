from django import forms
from django.forms import widgets
from django.forms.models import ModelForm
from accounts.models import Solicitation
from django.contrib.auth import get_user_model

class SolicitationForm(forms.ModelForm): 
    '''Essa classe é um formulário de criação de solicitações'''
    
    user = forms.ModelChoiceField(get_user_model().objects.all(), disabled=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(SolicitationForm, self).__init__(*args, **kwargs)

        # Inserindo atributo "help_text" ao campo do form "message"
        self.fields['message'].help_text = "Escreva uma mensagem breve que justifique a sua intenção de se tornar contribuidor do Herbário Virtual. É possível citar o envolvimento em estudos e/ou trabalhos relacionados com plantas daninhas."
        
    class Meta:
        model = Solicitation
        fields = ['user', 'message']