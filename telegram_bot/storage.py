import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class AIMediaStorage(FileSystemStorage):
    """Guarda as imagens do bot em settings.AI_MEDIA_ROOT (media-ia/), fora do MEDIA_ROOT.

    A pasta não é servida pelo site: o banco guarda só o caminho relativo, e o
    admin mostra a imagem por uma view restrita à equipe (ver admin.py).

    O local é lido do settings a cada acesso, e não fixado na importação, para
    que override_settings(AI_MEDIA_ROOT=...) funcione nos testes.
    """

    @property
    def base_location(self):
        return self._value_or_setting(self._location, settings.AI_MEDIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError("As imagens de media-ia/ não têm URL pública")
