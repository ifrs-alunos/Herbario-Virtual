"""Validadores compartilhados pelos dois herbários."""

from django.core.exceptions import ValidationError

# As fotos do acervo aparecem em destaque na página da planta/doença, e a miniatura
# é derivada delas por core.utils.make_small_image. Abaixo de Full HD o resultado
# fica visivelmente ruim, e é por isso que o mínimo existe.
MIN_WIDTH = 1920
MIN_HEIGHT = 1080


def validate_min_resolution(imagem):
    """Recusa imagem abaixo de 1920x1080.

    É um validador de campo de modelo: roda no `full_clean()` e, por tabela, em
    todo `ModelForm` que inclua o campo — as telas de contribuição do painel e
    também os inlines do `/admin/`. Assim a checagem existe num lugar só, em vez
    de uma cópia por formulário.

    Antes disso a única barreira era o `ValueError` levantado dentro de
    `Photo.save()`, que já não tinha como virar mensagem de formulário: chegava ao
    contribuidor como erro 500 depois de o upload inteiro ter subido.
    """

    try:
        largura, altura = imagem.width, imagem.height
    except Exception:
        # Arquivo ilegível, ausente ou que não é imagem. O próprio ImageField já
        # reclama disso; duplicar a mensagem aqui só confundiria.
        return

    if largura < MIN_WIDTH or altura < MIN_HEIGHT:
        raise ValidationError(
            'A imagem precisa ter no mínimo %(min_largura)sx%(min_altura)s pixels '
            '(Full HD). A enviada tem %(largura)sx%(altura)s.',
            code='resolucao_minima',
            params={
                'min_largura': MIN_WIDTH,
                'min_altura': MIN_HEIGHT,
                'largura': largura,
                'altura': altura,
            },
        )
