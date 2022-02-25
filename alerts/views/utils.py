import datetime

import django
from django.db.models import QuerySet, Q
from django.utils import timezone
from typing import List

tz = timezone.get_current_timezone()

from alerts.models import Report, Station


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

    return Report.objects.create(
        station_id=int(m_params.pop("chip_id", None)[0]),

        board_time=datetime.datetime.now(tz=tz),

        **clean_fields(m_params)
    )


def get_average_object_per_hour(model,
                                start_date: datetime.datetime,
                                end_date: datetime.datetime) -> List[django.db.models.Model]:
    objects = model.objects.filter(Q(board_time__gte=start_date) & Q(board_time__lte=end_date))

    first_object_date = objects.first().board_time
    object_fields = objects.first().get_fields(exclude=['id', 'station', 'station_id', 'board_time'])

    average_object_list = []

    tz_object = timezone.get_current_timezone()

    start_hour = first_object_date.replace(minute=0, second=0, microsecond=0)
    hour_count = (objects.last().board_time.replace(
        minute=0, second=0, microsecond=0) - start_hour).seconds // 3600
    datetime_range = [start_hour + datetime.timedelta(hours=i) for i in range(hour_count)]
    for dt in datetime_range:
        objects_in_hour = objects.filter(board_time__gte=dt, board_time__lt=dt + datetime.timedelta(hours=1))
        if objects_in_hour.count() > 0:
            values = {
                "station": Station.objects.get(id=objects_in_hour.first().station_id),
                "station_id": objects_in_hour.first().station_id,
                "board_time": dt
            }
            for field in object_fields:
                field_values = objects_in_hour.values_list(field, flat=True)
                if field_values[0] is not None:
                    values[field] = (sum(field_values) / len(field_values))
                else:
                    values[field] = None
            average_object_list.append(model(**values))

    return average_object_list


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
