from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from alerts.geo import GeocodingResult, haversine_km
from alerts.models import InterestPoint, Station
from dashboard.forms.interest_point_form import InterestPointForm

# Vacaria - RS e um ponto ~11 km ao norte (0,1° de latitude)
VACARIA = (-28.5122, -50.9339)
NORTE_11KM = (-28.4122, -50.9339)

GEOCODE = "dashboard.forms.interest_point_form.geocode"
GEOCODE_VIEW = "dashboard.views.interest_points.geocode"


def criar_profile(username):
    user = User.objects.create_user(username, f"{username}@exemplo.com", "senha-de-teste")
    return Profile.objects.get(user=user)


class HaversineTest(TestCase):
    def test_um_decimo_de_grau_de_latitude(self):
        self.assertAlmostEqual(haversine_km(*VACARIA, *NORTE_11KM), 11.12, places=1)

    def test_mesmo_ponto(self):
        self.assertEqual(haversine_km(*VACARIA, *VACARIA), 0)


class InterestPointModelTest(TestCase):
    def setUp(self):
        self.profile = criar_profile("maria")
        self.estacao = Station.objects.create(station_id="est-1", alias="Centro",
                                              lat_coordinate=VACARIA[0], lon_coordinate=VACARIA[1])
        self.estacao_norte = Station.objects.create(station_id="est-2", alias="Norte",
                                                    lat_coordinate=NORTE_11KM[0], lon_coordinate=NORTE_11KM[1])
        self.estacao_longe = Station.objects.create(station_id="est-3", alias="Longe",
                                                    lat_coordinate=-29.5, lon_coordinate=-51.0)
        Station.objects.create(station_id="est-4", alias="Sem coordenadas")

    def ponto(self, **kwargs):
        return InterestPoint(profile=self.profile, name="Ponto", **kwargs)

    def test_raio_padrao_e_20km(self):
        self.assertEqual(self.ponto().radius_km, 20)

    def test_estacao_obrigatoria_no_tipo_estacao(self):
        with self.assertRaises(ValidationError) as ctx:
            self.ponto(kind=InterestPoint.Kind.STATION).clean()
        self.assertIn("station", ctx.exception.message_dict)

    def test_coordenadas_obrigatorias_no_tipo_coordenadas(self):
        with self.assertRaises(ValidationError) as ctx:
            self.ponto(kind=InterestPoint.Kind.COORDINATES, latitude=-28.5).clean()
        self.assertIn("latitude", ctx.exception.message_dict)

    def test_endereco_obrigatorio_nos_tipos_de_endereco(self):
        for kind in InterestPoint.ADDRESS_KINDS:
            with self.assertRaises(ValidationError) as ctx:
                self.ponto(kind=kind, latitude=-28.5, longitude=-50.9).clean()
            self.assertIn("address", ctx.exception.message_dict)

    def test_ponto_de_estacao_descarta_endereco_e_coordenadas(self):
        ponto = self.ponto(kind=InterestPoint.Kind.STATION, station=self.estacao_norte,
                           address="Rua X", latitude=1, longitude=2)
        ponto.clean()
        self.assertEqual((ponto.address, ponto.latitude, ponto.longitude), ("", None, None))
        self.assertEqual(ponto.coordinates, NORTE_11KM)

    def test_ponto_de_coordenadas_descarta_estacao_e_endereco(self):
        ponto = self.ponto(kind=InterestPoint.Kind.COORDINATES, station=self.estacao,
                           address="Rua X", latitude=-28.5, longitude=-50.9)
        ponto.clean()
        self.assertIsNone(ponto.station)
        self.assertEqual(ponto.address, "")

    def test_estacoes_dentro_do_raio(self):
        ponto = self.ponto(kind=InterestPoint.Kind.COORDINATES, latitude=VACARIA[0], longitude=VACARIA[1])

        ponto.radius_km = 20
        self.assertEqual([s.alias for s, _ in ponto.stations_in_range()], ["Centro", "Norte"])

        ponto.radius_km = 5
        self.assertEqual([s.alias for s, _ in ponto.stations_in_range()], ["Centro"])

    def test_ponto_de_estacao_inclui_a_propria_estacao(self):
        ponto = self.ponto(kind=InterestPoint.Kind.STATION, station=self.estacao_norte, radius_km=1)
        [(estacao, distancia)] = ponto.stations_in_range()
        self.assertEqual((estacao, distancia), (self.estacao_norte, 0))


class InterestPointFormTest(TestCase):
    def dados(self, **kwargs):
        dados = {"name": "Sede", "kind": "rural_address", "address": "Linha São Pedro, Vacaria - RS",
                 "latitude": "", "longitude": "", "station": "", "radius_km": 20}
        dados.update(kwargs)
        return dados

    @patch(GEOCODE, return_value=GeocodingResult(-28.4, -50.8, "Vacaria"))
    def test_endereco_sem_coordenadas_e_geocodificado(self, geocode):
        form = InterestPointForm(self.dados())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.instance.latitude, form.instance.longitude), (-28.4, -50.8))
        geocode.assert_called_once_with("Linha São Pedro, Vacaria - RS")

    @patch(GEOCODE, return_value=None)
    def test_endereco_nao_encontrado_pede_para_marcar_no_mapa(self, geocode):
        form = InterestPointForm(self.dados())
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors["address"]), 1)
        self.assertIn("Clique no mapa", form.errors["address"][0])

    @patch(GEOCODE)
    def test_coordenadas_marcadas_no_mapa_prevalecem(self, geocode):
        form = InterestPointForm(self.dados(latitude="-28.45", longitude="-50.95"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.instance.latitude, form.instance.longitude), (-28.45, -50.95))
        geocode.assert_not_called()

    def test_estacao_sem_coordenadas_nao_e_opcao(self):
        Station.objects.create(station_id="sem", alias="Sem coordenadas")
        com = Station.objects.create(station_id="com", alias="Com", lat_coordinate=-28, lon_coordinate=-50)
        self.assertEqual(list(InterestPointForm().fields["station"].queryset), [com])

    def test_raio_fora_dos_limites(self):
        for raio in (0, 501):
            form = InterestPointForm(self.dados(kind="coordinates", latitude="-28", longitude="-50", radius_km=raio))
            self.assertIn("radius_km", form.errors)


class InterestPointViewsTest(TestCase):
    def setUp(self):
        self.maria = criar_profile("maria")
        self.joao = criar_profile("joao")
        self.ponto_joao = InterestPoint.objects.create(
            profile=self.joao, name="Ponto do João", kind=InterestPoint.Kind.COORDINATES,
            latitude=-28.5, longitude=-50.9,
        )
        self.client.force_login(self.maria.user)

    def test_exige_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:interest_point_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dashboard:login"), response.url)

    def test_usuario_comum_ve_o_item_no_menu(self):
        response = self.client.get(reverse("dashboard:interest_point_list"))
        self.assertContains(response, 'href="{}"'.format(reverse("dashboard:interest_point_list")))

    def test_lista_so_os_proprios_pontos(self):
        InterestPoint.objects.create(profile=self.maria, name="Ponto da Maria", kind="coordinates",
                                     latitude=-28.4, longitude=-50.8)
        response = self.client.get(reverse("dashboard:interest_point_list"))
        self.assertContains(response, "Ponto da Maria")
        self.assertNotContains(response, "Ponto do João")

    def test_cadastro_fica_com_o_usuario_logado(self):
        response = self.client.post(reverse("dashboard:interest_point_add"), {
            "name": "Talhão", "kind": "coordinates", "latitude": "-28.4", "longitude": "-50.8",
            "address": "", "station": "", "radius_km": 15,
        })
        self.assertRedirects(response, reverse("dashboard:interest_point_list"))
        ponto = InterestPoint.objects.get(name="Talhão")
        self.assertEqual((ponto.profile, ponto.radius_km), (self.maria, 15))

    def test_nao_edita_nem_exclui_ponto_de_outro_usuario(self):
        edit = reverse("dashboard:interest_point_edit", args=[self.ponto_joao.pk])
        delete = reverse("dashboard:interest_point_delete", args=[self.ponto_joao.pk])
        self.assertEqual(self.client.get(edit).status_code, 404)
        self.assertEqual(self.client.post(delete).status_code, 404)
        self.assertTrue(InterestPoint.objects.filter(pk=self.ponto_joao.pk).exists())

    def test_exclui_o_proprio_ponto(self):
        self.client.force_login(self.joao.user)
        delete = reverse("dashboard:interest_point_delete", args=[self.ponto_joao.pk])
        self.assertEqual(self.client.get(delete).status_code, 405)
        self.assertRedirects(self.client.post(delete), reverse("dashboard:interest_point_list"))
        self.assertFalse(InterestPoint.objects.filter(pk=self.ponto_joao.pk).exists())

    @patch(GEOCODE_VIEW, return_value=GeocodingResult(-28.4, -50.8, "Vacaria, RS"))
    def test_localizar_endereco(self, geocode):
        response = self.client.get(reverse("dashboard:interest_point_geocode"), {"q": "Vacaria"})
        self.assertEqual(response.json(), {"found": True, "lat": -28.4, "lon": -50.8, "display_name": "Vacaria, RS"})

    @patch(GEOCODE_VIEW, return_value=None)
    def test_localizar_endereco_nao_encontrado(self, geocode):
        response = self.client.get(reverse("dashboard:interest_point_geocode"), {"q": "xyz"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"found": False})


class MapInterestPointsTest(TestCase):
    def setUp(self):
        self.maria = criar_profile("maria")
        self.estacao = Station.objects.create(station_id="est-1", alias="Centro",
                                              lat_coordinate=VACARIA[0], lon_coordinate=VACARIA[1])
        InterestPoint.objects.create(profile=self.maria, name="Na estação", kind="station", station=self.estacao)
        InterestPoint.objects.create(profile=criar_profile("joao"), name="Do João", kind="coordinates",
                                     latitude=-28.4, longitude=-50.8)

    def test_mapa_mostra_os_pontos_do_usuario_logado(self):
        self.client.force_login(self.maria.user)
        response = self.client.get(reverse("alerts:map_url"))
        self.assertEqual(response.context["interest_points"], [{
            "name": "Na estação", "kind": "Estação", "location": "Centro", "radius_km": 20,
            "lat": VACARIA[0], "lon": VACARIA[1],
        }])
        self.assertContains(response, 'id="interest-points-data"')

    def test_visitante_nao_ve_pontos(self):
        response = self.client.get(reverse("alerts:map_url"))
        self.assertEqual(response.context["interest_points"], [])


class MapTilesTest(TestCase):
    """O fundo dos mapas vem do OpenStreetMap, sem conta nem token de terceiros"""

    def test_mapa_usa_openstreetmap_e_envia_a_origem(self):
        response = self.client.get(reverse("alerts:map_url"))
        self.assertContains(response, "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertContains(response, '<meta name="referrer" content="strict-origin-when-cross-origin">')
        self.assertNotContains(response, "mapbox")
        self.assertNotContains(response, "access_token")

    def test_tela_de_cadastro_usa_openstreetmap_e_envia_a_origem(self):
        self.client.force_login(criar_profile("maria").user)
        response = self.client.get(reverse("dashboard:interest_point_add"))
        self.assertContains(response, "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertContains(response, '<meta name="referrer" content="strict-origin-when-cross-origin">')
