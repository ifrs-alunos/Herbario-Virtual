from typing import List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from alerts.geo import haversine_km

from .base import BaseModel

DEFAULT_RADIUS_KM = 20
MAX_RADIUS_KM = 500


class InterestPoint(BaseModel):
    """Local de interesse de um usuário para o recebimento de alertas.

    O ponto é um endereço (urbano ou rural), um par de coordenadas ou uma estação
    já cadastrada. A ideia é que o usuário receba os alertas da estação escolhida
    e das estações que estiverem a até `radius_km` do ponto — ver
    `stations_in_range()`.

    Pontos de endereço guardam as coordenadas encontradas na geocodificação (ou
    marcadas no mapa). Pontos de estação não guardam coordenadas: usam as da
    estação, para acompanhar uma eventual correção no cadastro dela.
    """

    class Kind(models.TextChoices):
        URBAN_ADDRESS = "urban_address", "Endereço urbano"
        RURAL_ADDRESS = "rural_address", "Endereço rural"
        COORDINATES = "coordinates", "Coordenadas"
        STATION = "station", "Estação"

    ADDRESS_KINDS = (Kind.URBAN_ADDRESS, Kind.RURAL_ADDRESS)

    profile = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="interest_points",
        verbose_name="Usuário",
    )
    name = models.CharField("Nome", max_length=100, help_text="Ex.: Sede da propriedade, Talhão norte...")
    kind = models.CharField("Tipo de localização", max_length=20, choices=Kind.choices, default=Kind.URBAN_ADDRESS)
    address = models.CharField("Endereço", max_length=255, blank=True)
    latitude = models.FloatField(
        "Latitude", null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.FloatField(
        "Longitude", null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    station = models.ForeignKey(
        "alerts.Station",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="interest_points",
        verbose_name="Estação",
    )
    radius_km = models.PositiveSmallIntegerField(
        "Raio de interesse (km)",
        default=DEFAULT_RADIUS_KM,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_RADIUS_KM)],
        help_text="Estações a até esta distância do ponto também geram alertas.",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Ponto de interesse"
        verbose_name_plural = "Pontos de interesse"
        ordering = ["name", "pk"]

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()}, {self.radius_km} km)"

    def clean(self):
        errors = {}

        if self.kind == self.Kind.STATION:
            if not self.station_id:
                errors["station"] = "Escolha uma estação."
            elif self.station.lat_coordinate is None or self.station.lon_coordinate is None:
                errors["station"] = "Esta estação não tem coordenadas cadastradas."
        else:
            if self.kind in self.ADDRESS_KINDS and not self.address.strip():
                errors["address"] = "Informe o endereço."
            if self.latitude is None or self.longitude is None:
                if self.kind == self.Kind.COORDINATES:
                    errors["latitude"] = "Informe a latitude e a longitude do ponto."
                else:
                    errors.setdefault(
                        "address",
                        "Não encontramos este endereço. Clique no mapa para marcar o local do ponto.",
                    )

        if errors:
            raise ValidationError(errors)

        # Descarta o que não pertence ao tipo escolhido, para não sobrar lixo de
        # uma troca de tipo na edição.
        if self.kind == self.Kind.STATION:
            self.address = ""
            self.latitude = None
            self.longitude = None
        else:
            self.station = None
            if self.kind == self.Kind.COORDINATES:
                self.address = ""

    @property
    def coordinates(self) -> Optional[Tuple[float, float]]:
        if self.kind == self.Kind.STATION:
            if self.station is None or self.station.lat_coordinate is None or self.station.lon_coordinate is None:
                return None
            return self.station.lat_coordinate, self.station.lon_coordinate

        if self.latitude is None or self.longitude is None:
            return None
        return self.latitude, self.longitude

    @property
    def location_label(self) -> str:
        """Descrição curta da localização, para listas e tooltips"""
        if self.kind == self.Kind.STATION:
            return (self.station.alias or self.station.station_id) if self.station else "-"
        if self.kind in self.ADDRESS_KINDS:
            return self.address
        return f"{self.latitude:.6f}, {self.longitude:.6f}" if self.coordinates else "-"

    def stations_in_range(self, stations=None) -> List[Tuple["Station", float]]:  # noqa: F821
        """Estações a até `radius_km` do ponto, com a distância em km, da mais
        perto para a mais longe. Num ponto de estação, a própria estação é a
        primeira da lista (distância zero)."""
        from .station import Station

        origin = self.coordinates
        if origin is None:
            return []

        if stations is None:
            stations = Station.objects.filter(lat_coordinate__isnull=False, lon_coordinate__isnull=False)

        found = []
        for station in stations:
            if station.lat_coordinate is None or station.lon_coordinate is None:
                continue
            distance = haversine_km(origin[0], origin[1], station.lat_coordinate, station.lon_coordinate)
            if distance <= self.radius_km:
                found.append((station, distance))

        return sorted(found, key=lambda item: item[1])
