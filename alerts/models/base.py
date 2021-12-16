from django.db.models import Model
from typing import Tuple


class BaseModel(Model):
    def get_fields(self, exclude: Tuple[str] = ()) -> list:
        """
        :param exclude: campos que serão excluídos da lista retornada
        :return: lista de todos os campos do objeto
        """
        return [i.name for i in self._meta.fields if i.name not in exclude]

    class Meta:
        abstract = True
