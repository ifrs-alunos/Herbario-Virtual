from enum import Enum

from django.db import models
from django.db.models import Avg
from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from django.utils import timezone


class Period(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class AggregatorManager(models.Manager):
    def aggregate_by(self, period: str = Period.DAY.value, dt: timezone.datetime = None):
        if not dt:
            dt = timezone.now()

        period = Period(period)

        if period == Period.DAY:
            return self.filter(
                time__day=dt.day,
                time__year=dt.year,
                time__month=dt.month,
            ).values("date", "value")

        elif period == Period.WEEK:
            start_date = dt - timezone.timedelta(days=dt.weekday())

            return self.filter(time__range=[start_date, dt]) \
                .annotate(day=TruncDay('time')) \
                .values('day') \
                .annotate(avg_value=Avg('value')) \
                .order_by('day')

        elif period == Period.MONTH:
            start_date = dt.replace(day=1)

            return self.filter(time__range=[start_date, dt]) \
                .annotate(day=TruncDay('time')) \
                .values('day') \
                .annotate(avg_value=Avg('value')) \
                .order_by('day')

        elif period == Period.YEAR:
            start_date = dt.replace(month=1, day=1)

            return self.filter(time__range=[start_date, dt]) \
                .annotate(month=TruncMonth('time')) \
                .values('month') \
                .annotate(avg_value=Avg('value')) \
                .order_by('month')

        elif period == Period.ALL:
            return self.all().values("date", "value")

    def aggregate_hours(self, hours, end_dt: timezone.datetime = None):
        if not end_dt:
            end_dt = timezone.now()

        start_dt = end_dt - timezone.timedelta(hours=hours)

        return self.filter(time__range=[start_dt, end_dt]) \
            .annotate(hour=TruncHour('time')) \
            .values('hour') \
            .annotate(avg_value=Avg('value')) \
            .order_by('hour')
