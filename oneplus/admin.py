from django.contrib import admin
from content.admin import TestingQuestionAdmin, TestingQuestion


class TestingQuestionLinkAdmin(TestingQuestionAdmin):
    list_display = ("bank", "order", "name", "description", "preview_link")

    def preview_link(self, question):
        return u'<a href="/preview/%s">Preview</a>' % question.id
    preview_link.allow_tags = True
    preview_link.short_description = "Preview"

admin.site.unregister(TestingQuestion)
admin.site.register(TestingQuestion, TestingQuestionLinkAdmin)