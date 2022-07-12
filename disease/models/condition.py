from django.db import models
from disease.models.disease import Disease


class Condition(models.Model):
    """Esta classe define os dados de uma condição de uma doença."""

    characteristic = models.ForeignKey("accounts.CharSolicitationModel", null=True, on_delete=models.CASCADE)
    float_value = models.FloatField(blank=True, null=True)
    str_value = models.CharField(blank=True, null=True, max_length=100)
    bool_value = models.BooleanField(blank=True, null=True)

    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)

    def value(self):
        if self.characteristic.char_kind == 'float':
            return self.float_value
        elif self.characteristic.char_kind == 'str':
            return self.str_value
        else:
            return self.bool_value

    def val_to_str(self):
        return str(self.value()).replace(",", '.')

    def set_value(self, value):
        if self.characteristic.char_kind == 'float':
            self.float_value = value
        elif self.characteristic.char_kind == 'str':
            self.str_value = value
        else:
            self.bool_value = value
