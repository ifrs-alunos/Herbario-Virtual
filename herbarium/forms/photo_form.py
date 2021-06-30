from django import forms
from herbarium.models import Photo

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        exclude = ['published']
