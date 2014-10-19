from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from content.admin import TestingQuestionAdmin, TestingQuestion
from content.models import TestingQuestion
from auth.admin import LearnerResource, LearnerAdmin, Learner
from oneplus.utils import update_metric
from import_export import fields
from django.db.models import Q
from organisation.models import School


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
        return u'<a href="%s">Preview</a>' % reverse(
            'learn.preview',
            kwargs={'questionid': question.id}
        )
    preview_link.allow_tags = True
    preview_link.short_description = "Preview"

    def get_urls(self):
        urls = super(TestingQuestionLinkAdmin, self).get_urls()
        return [
            url(r'^add/preview/$',
                self.admin_site.admin_view(self.preview_add_view),
                name='preview_add'),
            url(r'^(?P<object_id>\d+)/preview/$',
                self.admin_site.admin_view(self.preview_change_view),
                name='preview_change')
        ] + urls

    def add_view(self, request, form_url='', extra_context=None):
        return super(TestingQuestionLinkAdmin, self).add_view(
            request,
            form_url=form_url or reverse('admin:preview_add'),
            extra_context=extra_context
        )

    @method_decorator(require_POST)
    def preview_add_view(self, request):
        form = self.get_form(request)
        form = form(request.POST)
        if form.is_valid():
            # use the form data to render the preview page
            # instead of the saved object
            from django.http import HttpResponse
            return HttpResponse("Hello World")
        return self.add_view(request)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(TestingQuestionLinkAdmin, self).change_view(
            request,
            object_id,
            form_url=form_url or reverse('admin:preview_change',
                                         kwargs={'object_id': object_id}),
            extra_context=extra_context
        )

    @method_decorator(require_POST)
    def preview_change_view(self, request, object_id):
        form = self.get_form(request)
        instance = TestingQuestion.objects.get(id=object_id)
        form = form(request.POST, instance=instance)
        if form.is_valid():
            # use the form data to render the preview page
            # instead of the saved object
            from django.http import HttpResponse
            return HttpResponse("Hello World")
        return self.change_view(request, object_id)


admin.site.unregister(TestingQuestion)
admin.site.unregister(Learner)
admin.site.register(TestingQuestion, TestingQuestionLinkAdmin)
admin.site.register(Learner, OnePlusLearnerAdmin)
