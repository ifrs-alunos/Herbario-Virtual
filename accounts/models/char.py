from django.db import models
from .char_solicitation_model import CharSolicitationModel

class Characteristic(models.Model):
    model = models.ForeignKey(CharSolicitationModel, on_delete=models.DO_NOTHING)
    _value = models.CharField(max_length=100)

    def get_value(self):
        if self.model.char_kind == 'int':
            value = int(self.value)

        elif self.model.char_kind == 'float':
            value = float(self.value)

        elif self.model.char_kind == 'str':
            value = self.value

        return value



