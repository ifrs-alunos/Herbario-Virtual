from django import forms
from core.models import PhotoPublication, Publication


class PublicationPhotoForm(forms.ModelForm):
    class Meta:
        model = PhotoPublication
        fields = '__all__'

    # Sobscrevendo o metodo clean pra retornar no form quando salvo um Publication object não um numero
    def clean(self):
        cleaned_data = super(PublicationPhotoForm, self).clean()
        cleaned_data['publication'] = Publication.objects.get(id=cleaned_data['publication'])
        return cleaned_data

    # Sobscrever o metodo __init__ para mostrar a cultura junto com o nome da doença
    def __init__(self, *args, **kwargs):
        super(PublicationPhotoForm, self).__init__(*args, **kwargs)
        queryset = Publication.objects.all()
        publications = [(i.id, f'{i.title}') for i in queryset]
        self.fields['publication'] = forms.ChoiceField(choices=publications, label='Publicação')
