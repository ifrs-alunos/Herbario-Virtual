from django import forms

from disease.models import Culture, Disease


class AIModelApprovalForm(forms.Form):
    """Categorização de uma imagem de treino ao aprová-la: planta, doença e estado.

    A planta é a cultura da doença (Culture). O estado pode ser um dos que a
    doença já lista em Disease.states ou um novo, digitado na hora, que passa a
    fazer parte da lista daquela doença.
    """

    culture = forms.ModelChoiceField(queryset=Culture.objects.all(), label="Planta")
    disease = forms.ModelChoiceField(queryset=Disease.objects.select_related('culture_disease'), label="Doença")
    state = forms.CharField(max_length=60, required=False, label="Estado")
    new_state = forms.CharField(max_length=60, required=False, label="Novo estado")

    def clean(self):
        data = super().clean()
        culture, disease = data.get('culture'), data.get('disease')
        state = (data.get('state') or '').strip()
        new_state = (data.get('new_state') or '').strip()

        if culture and disease and disease.culture_disease_id != culture.pk:
            raise forms.ValidationError(
                "A doença \"{}\" não é da planta \"{}\".".format(disease, culture))

        if state and new_state:
            raise forms.ValidationError("Escolha um estado existente ou digite um novo, não os dois.")
        if not state and not new_state:
            raise forms.ValidationError("Informe o estado da planta na imagem.")

        if state and disease and state not in disease.states:
            raise forms.ValidationError(
                "O estado \"{}\" não pertence à doença \"{}\".".format(state, disease))

        data['state'], data['new_state'] = state, new_state
        return data

    def get_state(self):
        """O estado escolhido, ou o digitado, já acrescentado à lista da doença.

        Chamar dentro de uma transação: a doença é travada para que dois
        administradores criando estados ao mesmo tempo não percam um deles.
        """

        if self.cleaned_data['state']:
            return self.cleaned_data['state']

        disease = Disease.objects.select_for_update().get(pk=self.cleaned_data['disease'].pk)
        state = disease.add_state(self.cleaned_data['new_state'])
        # A view repassa cleaned_data['disease'] para a aprovação: precisa da lista nova
        self.cleaned_data['disease'] = disease

        return state
