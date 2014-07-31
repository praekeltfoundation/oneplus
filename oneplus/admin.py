from django.contrib import admin
from content.admin import TestingQuestionAdmin, TestingQuestion
from auth.admin import LearnerResource, LearnerAdmin, Learner
from oneplus.utils import update_metric
from import_export import fields
from django.db.models import Q
from organisation.models import School


class OnePlusLearnerResource(LearnerResource):
    course = fields.Field(column_name=u'course')
    completed_questions = fields.Field(column_name=u'completed_questions')
    percentage_correct = fields.Field(column_name=u'percentage_correct')

    def import_obj(self, obj, data, dry_run):
        school, created = School.objects.get_or_create(name=data[u'school'])
        data[u'school'] = school.id
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


class TestingQuestionLinkAdmin(TestingQuestionAdmin):
    list_display = TestingQuestionAdmin.list_display + ("preview_link",)

    def preview_link(self, question):
        return u'<a href="/preview/%s">Preview</a>' % question.id
    preview_link.allow_tags = True
    preview_link.short_description = "Preview"

admin.site.unregister(TestingQuestion)
admin.site.unregister(Learner)
admin.site.register(TestingQuestion, TestingQuestionLinkAdmin)
admin.site.register(Learner, OnePlusLearnerAdmin)
