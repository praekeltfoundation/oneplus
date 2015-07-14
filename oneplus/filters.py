from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from core.models import Participant
from datetime import datetime, timedelta
import calendar


class LearnerActiveFilter(admin.SimpleListFilter):
    title = _("Active/Inactive")
    parameter_name = "acic"

    def lookups(self, request, model_admin):
        return [
            ("a", _("Active")),
            ("i", _("Inactive")),
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == "a":
            return queryset.filter(last_active_date__isnull=False)
        elif self.value() == "i":
            return queryset.filter(last_active_date__isnull=True)


class LearnerPercentageCorrectFilter(admin.SimpleListFilter):
    title = _("Percentage Correct")
    parameter_name = "pc"

    def lookups(self, request, model_admin):
        return get_percentage_lookups()

    def get_learners(self, value, timeframe):
        min, max = get_perc_min_max(value)

        qry = """
            coalesce((select sum(coalesce(correct%s, 0)) * 100 / count(1)
            from core_participantquestionanswer qa
            where qa.participant_id = core_participant.id
        """ % get_sum_boolean_cast_string()

        if timeframe:
            start, end = get_timeframe_range(timeframe)

            qry += "and answerdate between %s and %s"

        qry += "), 0 )"

        if timeframe:
            parts = Participant.objects\
                .extra(select={"perc": qry}, select_params=(start, end))\
                .extra(where=["(%s) between %s and %s" % (qry, min, max)], params=(start, end))
        else:
            parts = Participant.objects\
                .extra(select={"perc": qry})\
                .extra(where=["(%s) between %s and %s" % (qry, min, max)])

        return parts.values("id")

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            if "tf" in request.GET:
                timeframe = request.GET["tf"]
            else:
                timeframe = None

            return queryset.filter(participant__id__in=self.get_learners(self.value(), timeframe))


class LearnerPercentageOfQuestionsCompletedFilter(admin.SimpleListFilter):
    title = _("Percentage of Questions Completed")
    parameter_name = "pqc"

    def lookups(self, request, model_admin):
        return get_percentage_lookups()

    def get_learners(self, value):
        min, max = get_perc_min_max(value)

        qry = """
            select count(1) * 100 / ( trunc( date_part( 'day',now() - coalesce( datejoined, now() ) ) ) * 15 )
            from core_participantquestionanswer qa
            where qa.participant_id = core_participant.id
        """

        parts = Participant.objects\
            .extra(select={"perc": qry})\
            .extra(where=["(%s) between %s and %s" % (qry, min, max)])\
            .values("id")

        return parts

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__id__in=self.get_learners(self.value()))


class LearnerTimeFrameFilter(admin.SimpleListFilter):
    title = _("Timeframe")
    parameter_name = "tf"

    def lookups(self, request, model_admin):
        return [
            ("0", _("This week")),
            ("1", _("Last week")),
            ("2", _("This month")),
            ("3", _("Last month")),
            ("4", _("Last 3 months")),
            ("5", _("Last 6 months")),
            ("6", _("This year")),
            ("7", _("Last year")),
        ]

    def queryset(self, request, queryset):
        return queryset


def get_percentage_lookups():
    return [
        ("0", _("between 0 - 19%")),
        ("1", _("between 20 - 39%")),
        ("2", _("between 40 - 59%")),
        ("3", _("between 60 - 79%")),
        ("4", _("between 80 - 89%")),
        ("5", _("between 90 - 100%")),
    ]


def sub_months(src, months):
    months = abs(months)
    month = src.month - months
    year = src.year

    if month < 1:
        year -= abs(month - 12) / 12

    month %= 12

    if month == 0:
        month = 12

    day = min(src.day, calendar.monthrange(year, month)[1])
    return datetime(year=year, month=month, day=day)


def get_today():
    return datetime.now()


def get_timeframe_range(value):
    start = None
    end = None
    today = get_today()
    dw = today.weekday()

    if value == "1":
        # last week
        start = today - timedelta(days=dw, weeks=1)
        end = start + timedelta(6 - dw)


    elif value == "2":
        # this month
        start = today.replace(day=1)
        end = start.replace(day=calendar.monthrange(start.year, start.month)[1])

    elif value == "3":
        # last month
        start = sub_months(today, 1)
        end = start.replace(day=calendar.monthrange(start.year, start.month)[1])

    elif value == "4":
        # last 3 months
        start = sub_months(today, 2)
        end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    elif value == "5":
        # last 6 months
        start = sub_months(today, 5)
        end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    elif value == "6":
        # this year
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)

    elif value == "7":
        # last year
        start = today.replace(year=today.year - 1, month=1, day=1)
        end = start.replace(month=12, day=31)

    else:
        # this week
        start = today - timedelta(days=dw)
        end = start + timedelta(6 - dw)

    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start, end


def get_perc_min_max(value):
    if value == "1":
        min = 20
        max = 39
    elif value == "2":
        min = 40
        max = 59
    elif value == "3":
        min = 60
        max = 79
    elif value == "4":
        min = 80
        max = 89
    elif value == "5":
        min = 90
        max = 100
    else:
        min = 0
        max = 19

    return min, max


def get_sum_boolean_cast_string():
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        # summing of boolean fields in postgres require a cast to int
        return "::int"

    return ""


class LearnerLimitFilter(admin.SimpleListFilter):
    title = _("Limit")
    parameter_name = "lmt"

    def lookups(self, request, model_admin):
        return [
            ("0", _("5")),
            ("1", _("10")),
            ("2", _("25")),
            ("3", _("50")),
        ]

    def queryset(self, request, queryset):
        if "lmt" in request.GET and request.GET["lmt"]:
            limit = self.get_limit(request.GET["lmt"])
            id_list = list()
            count = 0
            for item in queryset:
                if count < limit:
                    id_list.append(item.id)
                else:
                    break
                count += 1

            return queryset.filter(id__in=id_list)
        else:
            return queryset

    def get_limit(self, value):
        limit_dict = [5, 10, 25, 50]
        return limit_dict[int(value)]