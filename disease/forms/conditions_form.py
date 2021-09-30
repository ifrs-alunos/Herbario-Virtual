from django import forms
from disease.models import Condition

class ConditionForm(forms.ModelForm):
    class Meta:
        model = Condition
        fields = '__all__'