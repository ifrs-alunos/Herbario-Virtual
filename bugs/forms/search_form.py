from django import forms

class SearchForm(forms.Form):
    text = forms.CharField(max_length=55, min_length=3, widget=forms.TextInput(attrs={'class':'form-control'}))
