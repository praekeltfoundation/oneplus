from django.contrib import admin
from django.conf import settings
from content.admin import TestingQuestionAdmin, TestingQuestion
from auth.admin import LearnerResource, LearnerAdmin
from auth.models import Learner
from oneplus.utils import update_metric
from import_export import fields
from django.db.models import Q, Count
from organisation.models import School
from django.contrib.admin.sites import AdminSite
from .filters import *

AdminSite.index_template = 'admin/my_index.html'


class OnePlusLearnerResource(LearnerResource):
    class_name = fields.Field(column_name=u'class')
    completed_questions = fields.Field(column_name=u'completed_questions')
    percentage_correct = fields.Field(column_name=u'percentage_correct')

    class Meta:
        model = Learner
        exclude = (
            'customuser_ptr', 'password', 'last_login', 'is_superuser',
            'groups', 'user_permissions', 'is_staff', 'is_active',
            'date_joined', 'unique_token', 'unique_token_expiry'
            'welcome_message_sent', 'welcome_message'
        )
        export_order = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'mobile',
            'school',
            'country',
            'area',
            'city',
            'optin_sms',
            'optin_email',
            'completed_questions',
            'percentage_correct',
            'class_name',
        )

    def import_obj(self, obj, data, dry_run):
        school, created = School.objects.get_or_create(name=data[u'school'])
        data[u'school'] = school.id
        data[u'mobile'] = data[u'username']
        return super(LearnerResource, self)\
            .import_obj(obj, data, dry_run)

    def import_data(self, dataset, **kwargs):

        if not kwargs["dry_run"]:
            count = dataset.height
            update_metric(
                "running.registered.participants",
                int(count),
                "SUM",
            )

        return super(LearnerResource, self).import_data(dataset, **kwargs)


class OnePlusLearnerAdmin(LearnerAdmin):
    resource_class = OnePlusLearnerResource

    list_display = LearnerAdmin.list_display + ("get_completed", "get_perc_correct")

    list_filter = (LearnerActiveFilter, LearnerPercentageCorrectFilter, LearnerPercentageOfQuestionsCompletedFilter,
                   LearnerTimeFrameFilter) + LearnerAdmin.list_filter

    def save_model(self, request, obj, form, change):
        before_total = Learner.objects.all().count()
        super(type(self), self).save_model(request, obj, form, change)
        total = Learner.objects.all().count()
        update_metric(
            "registered.participants",
            total,
            'LAST'
        )

        if total > 0:
            opt_ins = float(Learner.objects.filter(
                Q(optin_sms=True) | Q(optin_email=True)).count()) / float(total)

            update_metric(
                "percentage.optin",
                opt_ins * 100,
                'LAST'
            )

        if total != before_total:
            update_metric(
                "running.registered.participants",
                total - before_total,
                "SUM",
            )

    def get_completed(self, obj):
        return obj.total
    get_completed.short_description = "Completed"
    get_completed.admin_order_field = "total"

    def get_perc_correct(self, obj):
        return obj.perc
    get_perc_correct.short_description = "Percentage Correct"
    get_perc_correct.admin_order_field = "perc"

    @staticmethod
    def get_total_query(timeframe):
        qry = """
            select count(1)
            from core_participantquestionanswer pqa
            INNER JOIN core_participant p
                ON p.id = pqa.participant_id
                AND p.learner_id = auth_learner.customuser_ptr_id
        """

        if timeframe:
            qry += " where answerdate between %s and %s"

        return qry

    @staticmethod
    def get_perc_correct_query(timeframe):
        rep_str = get_sum_boolean_cast_string()

        qry = """
            coalesce((select sum(coalesce(correct%s, 0)) * 100 / count(1)
            from core_participantquestionanswer pqa
            INNER JOIN core_participant p
                ON p.id = pqa.participant_id
                AND p.learner_id = auth_learner.customuser_ptr_id
        """ % rep_str

        if timeframe:
            qry += " where answerdate between %s and %s"

        qry += "), 0)"

        return qry

    def queryset(self, request):
        if "tf" in request.GET:
            timeframe = request.GET["tf"]
        else:
            timeframe = None

        qs = super(LearnerAdmin, self).queryset(request)
        if timeframe:
            start, end = get_timeframe_range(timeframe)
            qs = qs.extra(select={"total": self.get_total_query(timeframe)}, select_params=(start, end))\
                .extra(select={"perc": self.get_perc_correct_query(timeframe)}, select_params=(start, end))
        else:
            qs = qs.extra(select={"total": self.get_total_query(timeframe)})\
                .extra(select={"perc": self.get_perc_correct_query(timeframe)})

        return qs

admin.site.unregister(Learner)
admin.site.register(Learner, OnePlusLearnerAdmin)
