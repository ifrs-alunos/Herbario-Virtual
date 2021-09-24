import datetime

from django.db.models import QuerySet
from django.utils import timezone

tz = timezone.get_current_timezone()

from assessment.models import Report, TempReport


def mean(array: list) -> float:
    """
    Retorna a média dos valores de uma lista, retirando os 10% mais altos e mais baixos

    :param array: lista de valores
    :return: média dos valores
    """

    dezporcento = len(array) // 10
    array = sorted(array)[dezporcento:-dezporcento]
    return sum(array) / len(array)


def create_report_from_params(params: dict) -> Report:
    """
    Cria um objeto Report na database a partir dos paramêtros passados pela requisição

    :param params: valor do atributo `POST` do objeto `request`
    :return: objeto da classe Report
    """

    m_params = dict(params)

    print(m_params)

    return Report.objects.create(
        station_id=int(m_params.pop("chip_id", None)[0]),

        board_time=datetime.datetime.now(tz=tz),

        **clean_fields(m_params)
    )


def get_average_values(temp_reports: QuerySet[TempReport]) -> Report:
    """
    processa os valores dos relatórios temporários e retorna um objeto
    com a média dos valores, excluindo os 10% mais altos e baixo

    :param temp_reports: lista de relatórios temporários
    :return: relatório com os valores médios de todas os os últimos relatórios temporários
    """

    dht11_humidity = []
    dht11_temperature = []
    dhtt11_heat_index = []

    bmp280_temperature = []
    bmp280_pressure = []
    bmp280_altitude = []

    ldr_light = []

    for i in temp_reports.order_by('-board_time'):
        dht11_humidity.append(i.dht11_humidity)
        dht11_temperature.append(i.dht11_temperature)
        dhtt11_heat_index.append(i.dhtt11_heat_index)

        bmp280_temperature.append(i.bmp280_temperature)
        bmp280_pressure.append(i.bmp280_pressure)
        bmp280_altitude.append(i.bmp280_altitude)

        ldr_light.append(i.ldr_light)

    return Report.objects.create(
        dht11_humidity=mean(dht11_humidity),
        dht11_temperature=mean(dht11_temperature),
        dhtt11_heat_index=mean(dhtt11_heat_index),

        bmp280_temperature=mean(bmp280_temperature),
        bmp280_pressure=mean(bmp280_pressure),
        bmp280_altitude=mean(bmp280_altitude),

        ldr_light=mean(ldr_light),

        board_time=temp_reports.first().board_time
    )


def to_datetime(date: str, time: str, until: bool = False) -> datetime.datetime:
    """
    :param date: string de data no formato 'aaaa-mm-dd' ou string vazia
    :param time: string de tempo no formato 'hh:mm' ou string vazia
    :param until: booleano que define se o valor da hora deve ser 00:00 ou o horário atual quando indefinido
    :return: objeto datetime montado a partir dos valores passados
    """

    now = datetime.datetime.now()

    if date == '':
        date = f"{now:%Y-%m-%d}"
    if time == '':
        if until:
            time = f"{now:%H:%M}"
        else:
            time = "00:00"

    parsed_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    return parsed_datetime


def clean_fields(params) -> dict:
    """
    limpa os campos (remove temperaturas fora do range de -20~80 graus) e retorna None caso não seja um número
    :param params: dicionario com os parametros "sujos"
    :return: parametros "limpos"
    """

    for key, value in params.items():
        value = value[0] if isinstance(value, list) else value
        try:
            # se a chave terminar com a letra h (umidade)
            if key.endswith("h"):
                params[key] = float(value) if (0 <= float(value) <= 100) else None

            # se a chave terminar com t (temperatura), hi (sensação térmica), ou p (pressão)
            elif key.split('_')[-1] in ('t', 'hi'):
                params[key] = float(value) if (-20 <= float(value) <= 80) else None
            elif key.split('_')[-1] in ('p', 'a', 'uv'):
                params[key] = float(value)
            else:
                params[key] = int(value)
        except TypeError:
            # caso seja impossivel converter de string para inteiro ou float, define o valor como None (nulo)
            params[key] = None

    return params


