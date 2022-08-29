from PIL import Image
from io import BytesIO
from django.core.files import File



def make_small_image(image, size=(854, 480)):
    """Esta função retorna uma imagem miniatura com um tamanho específico a partir de uma imagem maior"""

    im = Image.open(image)  # Abre a imagem com o Pillow

    im.convert('RGB')

    im.thumbnail(size)  # Redimensiona a imagem com o tamanho padrão descrito nos parâmetros

    thumb_io = BytesIO()  # Cria um objeto BytesIO

    im.save(thumb_io, 'JPEG', quality=100)  # Salva imagem para um objeto BytesIO

    thumbnail = File(thumb_io, name=image.name)  # Cria um objeto File 'amigável' ao Django

    return thumbnail