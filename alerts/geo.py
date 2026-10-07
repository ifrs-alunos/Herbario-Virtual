"""Cálculos de distância e geocodificação de endereços.

A geocodificação usa o Nominatim (OpenStreetMap), que é gratuito mas tem política
de uso: no máximo uma requisição por segundo e um User-Agent que identifique o
sistema. Por isso só é chamado quando o usuário pede — botão "Localizar" ou
salvar um ponto de endereço sem ter marcado o local no mapa.

Endereço rural costuma não ser encontrado (linha, estrada vicinal, km...). Nesses
casos o formulário pede que o usuário marque o ponto no mapa.
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0088

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GEOCODING_TIMEOUT = 8


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km entre dois pontos, pela fórmula de haversine"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@dataclass
class GeocodingResult:
    latitude: float
    longitude: float
    display_name: str


def geocode(address: str) -> Optional[GeocodingResult]:
    """Converte um endereço em coordenadas. Devolve None se não encontrar ou se o
    serviço falhar — quem chama decide o que dizer ao usuário."""
    address = (address or "").strip()
    if not address:
        return None

    try:
        response = requests.get(
            getattr(settings, "GEOCODING_URL", NOMINATIM_URL),
            params={
                "q": address,
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "br",
                "accept-language": "pt-BR",
            },
            headers={
                "User-Agent": getattr(settings, "GEOCODING_USER_AGENT", "Labfito/1.0 (IFRS Vacaria)"),
            },
            timeout=GEOCODING_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        logger.warning("Falha ao geocodificar o endereço %r", address, exc_info=True)
        return None

    if not results:
        return None

    first = results[0]
    return GeocodingResult(
        latitude=float(first["lat"]),
        longitude=float(first["lon"]),
        display_name=first.get("display_name", ""),
    )
