from auth.models import Learner
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import *
from core.models import Participant
from .utils import VumiSmsApi
from organisation.models import CourseModuleRel
from communication.forms import MessageCreationForm


class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description"]})
    ]


class PostAdmin(SummernoteModelAdmin):
    list_display = ("name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "course", "publishdate"]}),
        ("Content",
            {"fields": ["big_image", "small_image", "moderated", "content"]})
    ]


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("author", "content", "publishdate")
    ordering = ("publishdate",)

    def has_add_permission(self, request):
        return False


class ChatGroupAdmin(SummernoteModelAdmin):
    list_display = ("name", "course", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "course"]})
    ]
    inlines = (ChatMessageInline, )


class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("course", "module", "question", "author", "publishdate", "content", "moderated")
    list_filter = ("module", "question", "moderated")
    search_fields = ("author", "content")
    fieldsets = [
        (None,
            {"fields": ["name", "description"]}),
        ("Content",
            {"fields": ["content", "author", "publishdate", "moderated"]}),
        ("Discussion Group",
            {"fields": ["course", "module", "question", "response"]})
    ]


class MessageAdmin(SummernoteModelAdmin):
    list_display = ("name", "get_content", "get_class", "author", "direction", "publishdate", 'get_response')
    list_filter = ("direction", "responded")
    search_fields = ("name", )
    form = MessageCreationForm
    fieldsets = [
        (None,
            {"fields": ["name", ("to_course", "to_class", "users"), "direction", "publishdate", "content"]})
    ]

    def get_content(self, obj):
        return '<a href="">' + obj.content + '<a>'

    get_content.short_description = 'Message Content'
    get_content.allow_tags = True

    def get_class(self, obj):
        p = Participant.objects.select_related().filter(learner=obj.author)
        return ', '.join([obj.classs.name for obj in p.all()])

    get_class.short_description = 'Class'

    def get_response(self, obj):
        if obj.responded:
            return obj.responddate
        else:
            return '<a href="">Respond</a>'

    get_response.short_description = 'Response Sent'
    get_response.allow_tags = True

    class Media:
        js = ('js/auth.js', "grappelli/jquery/jquery-1.9.1.min.js")


class SmsAdmin(SummernoteModelAdmin):
    list_display = ("msisdn", "date_sent", "message")


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "get_name",
        "get_issue",
        "get_fix",
        "get_question",
        "get_module",
        "get_course",
        "get_author",
        "publish_date",
        "get_response",
    )

    def get_name(self, obj):
        return u'%s %s' % (obj.user.first_name, obj.user.last_name)
    get_name.short_description = "Name"

    def get_issue(self, obj):
        if obj.response is None:
            return obj.issue
        else:
            return u'<a href="">%s</a>' % obj.issue
    get_issue.allow_tags = True
    get_issue.short_description = "What is wrong with this question?"

    def get_fix(self, obj):
        if obj.response is None:
            return obj.fix
        else:
            return u'<a href="">%s</a>' % obj.fix
    get_fix.allow_tags = True
    get_fix.short_description = "How can we fix the problem?"

    def get_question(self, obj):
        return u'<p>%s</p><a href="/preview/%s">View Question</a>' % (obj.question.name, obj.question.id)
    get_question.allow_tags = True
    get_question.short_description = "Question"

    def get_module(self, obj):
        return obj.question.module.name
    get_module.short_description = "Module"

    def get_course(self, obj):
        course_module = CourseModuleRel.objects.filter(module=obj.question.module)
        courses = ""
        for c in course_module:
            courses = '<p>%s</p>' % c.course.name
        return u'%s' % courses
    get_course.allow_tags = True
    get_course.short_description = "Course"

    def get_author(self, obj):
        return obj.user.mobile
    get_author.short_description = "Author"

    def get_response(self, obj):
        if obj.response is None:
            return u'<p>None</p><a href="">Respond</a>'
        else:
            return obj.response.publish_date
    get_response.allow_tags = True
    get_response.short_description = "Response Sent"

# Communication
admin.site.register(Sms, SmsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatGroup, ChatGroupAdmin)
admin.site.register(Discussion, DiscussionAdmin)
admin.site.register(Report, ReportAdmin)
