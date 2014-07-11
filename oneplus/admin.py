from django.contrib import admin
from content.admin import TestingQuestionAdmin, TestingQuestion
from auth.admin import LearnerResource, LearnerAdmin, Learner
from oneplus.utils import update_metric


class OnePlusLearnerResource(LearnerResource):
    def after_save_instance(self, instance, dry_run):
        if dry_run is False:
            update_metric(
                "running.registered.participants",
                1,
                "SUM",
            )

class OnePlusLearnerAdmin(LearnerAdmin):
    resource_class = OnePlusLearnerResource

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