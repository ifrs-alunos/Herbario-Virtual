from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Button
from alerts.models import MathModel,Constant
from django import forms
from accounts.forms import ConstantModelForm

# Formset para criar novas constantes
ConstantFormset = forms.formset_factory(ConstantModelForm)

# Formset para editar constantes
ConstantEditFormset = forms.inlineformset_factory(MathModel,Constant,ConstantModelForm,extra=0)


class ConstantFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ConstantFormSetHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
            'name',
            'value',

        )
        self.add_input(Button('new_constant', "Adicionar nova constante", css_class='btn-light'))
        self.add_input(Button('delete_constant', "Deletar constante", css_class='btn-danger'))
        self.form_id = 'constant_formset'
        self.form_tag = False
        self.template = 'bootstrap4/table_inline_formset.html'

class ConstantFormSetEditHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ConstantFormSetEditHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
            'name',
            'value',

        )
        self.add_input(Button('new_constant', "Adicionar nova constante", css_class='btn-light'))
        self.form_id = 'constant_formset'
        self.form_tag = False
        self.template = 'bootstrap4/table_inline_formset.html'