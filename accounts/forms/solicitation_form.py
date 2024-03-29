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

        # Inserindo atributo "placeholder" ao campo do form "message"
        self.fields['message'].widget = forms.Textarea(attrs={"placeholder": "Escreva aqui uma mensagem breve que justifique a sua intenção de se tornar contribuidor do Herbário Virtual. É possível citar o envolvimento em estudos e/ou trabalhos relacionados com plantas daninhas."})

        # Adicionando o * ao atributo "term"
        label_term = self.fields['term'].label
        self.fields['term'].label = f'{label_term}*'
    class Meta:
        model = Solicitation
        fields = ['user', 'message','term']