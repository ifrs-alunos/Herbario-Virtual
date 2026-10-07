from django import forms

from alerts.geo import geocode
from alerts.models import InterestPoint, Station


class InterestPointForm(forms.ModelForm):
    """Cadastro de ponto de interesse. Os campos que valem para cada tipo são
    mostrados/escondidos pelo JavaScript da tela; quem descarta o resto é
    `InterestPoint.clean()`."""

    class Meta:
        model = InterestPoint
        fields = ["name", "kind", "address", "latitude", "longitude", "station", "radius_km"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "kind": forms.RadioSelect,
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "-28.512345"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "-50.934567"}),
            "station": forms.Select(attrs={"class": "form-select"}),
            "radius_km": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estação sem coordenadas não tem como ser ponto de interesse
        self.fields["station"].queryset = Station.objects.filter(
            lat_coordinate__isnull=False, lon_coordinate__isnull=False
        ).order_by("alias")
        self.fields["station"].empty_label = "Selecione uma estação"

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        address = (cleaned.get("address") or "").strip()

        if kind not in InterestPoint.ADDRESS_KINDS or not address:
            return cleaned

        # As coordenadas enviadas valem mais que o endereço: são o que o usuário
        # viu no mapa (a tela relocaliza o endereço quando ele é alterado, e o
        # ponto rural costuma ser marcado à mão). Só sem elas é que se tenta
        # achar o endereço. Se não achar, quem avisa o usuário é
        # InterestPoint.clean() — aqui não, para a mensagem não sair duplicada.
        if cleaned.get("latitude") is None or cleaned.get("longitude") is None:
            result = geocode(address)
            if result is not None:
                cleaned["latitude"] = result.latitude
                cleaned["longitude"] = result.longitude

        return cleaned
