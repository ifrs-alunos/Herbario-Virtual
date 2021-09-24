from django.db.models import Model
from typing import Tuple


class BaseModel(Model):
    def get_fields(self, exclude: Tuple[str] = ()) -> list:
        """
        :param exclude: fields to be excluded from the output
        :return: list of all fields of the object
        """
        return [i.name for i in self._meta.fields if i.name not in exclude]

    class Meta:
        abstract = True
