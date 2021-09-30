from django import forms

class SearchForm(forms.Form):
    text = forms.CharField(label='Buscar', required=False)
