from auth.models import Learner
from django.contrib import admin
from django.http.response import HttpResponseRedirect, HttpResponse
from django_summernote.admin import SummernoteModelAdmin
from .models import *
from core.models import Participant
from core.filters import UserFilter
from .utils import VumiSmsApi, get_user_bans
from organisation.models import CourseModuleRel
from .filters import *
from django.utils.http import urlquote


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
            {"fields": ["big_image", "small_image", "moderated", "content"]}),
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


class ChatMessageAdmin(SummernoteModelAdmin):
    list_display = ("id", "chatgroup", "author", "safe_content", "publishdate", "moderated")
    list_filter = ("chatgroup", "moderated")
    search_fields = (
        "content",
        "original_content",
        "author__first_name",
        "author__last_name",
        "author__username",
    )
    fieldsets = [
        (None,
            {"fields": ["chatgroup", "author", "content", "publishdate", "moderated"]}),
        ("Moderation",
            {"fields": ["original_content", "unmoderated_date", "unmoderated_by"]}),
    ]


class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("id", "get_question", "module", "course", "get_content",
                    "author", "publishdate", "get_response_posted", "moderated")
    list_filter = ("course", "module", "question", "moderated")
    search_fields = ("author__first_name", "author__last_name", "author__username", "author__mobile", "content")
    fieldsets = [
        (None,
            {"fields": ["name", "description"]}),
        ("Content",
            {"fields": ["content", "author", "publishdate", "moderated"]}),
        ("Moderation",
            {"fields": ["original_content", "unmoderated_date", "unmoderated_by"]}),
        ("Discussion Group",
            {"fields": ["course", "module", "question", "response"]})
    ]
    actions = ['respond_to_selected', 'moderate_selected']

    def respond_to_selected(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('/discussion_response_selected/%s' %
                                    ",".join(selected))

    respond_to_selected.short_description = 'Respond to selected'

    def moderate_selected(modeladmin, request, queryset):
        queryset.update(moderated=True)

    moderate_selected.short_description = 'Moderate selected'

    def get_question(self, obj):
        if obj.question:
            return u'<a href="/admin/content/testingquestion/%s" target="_blank">%s</a><br>' \
                   u'<a href="/preview/%s" target="_blank">' \
                   u'View Question</a>' % (obj.question.id, obj.question.name, obj.question.id)
        else:
            return u'None'

    get_question.short_description = 'Question'
    get_question.allow_tags = True

    def get_content(self, obj):
        return u'<a href="/discussion_response/%s" target="_blank">%s</a>' % (obj.id, obj.content)

    get_content.short_description = 'Content'
    get_content.allow_tags = True

    def get_response_posted(self, obj):
        if obj.response:
            return obj.response.publishdate
        else:
            return u'%s&nbsp&nbsp<a href="/discussion_response/%s" target="_blank">Respond</a>' % (None, obj.id)

    get_response_posted.short_description = 'Response Posted'
    get_response_posted.allow_tags = True


class MessageAdmin(SummernoteModelAdmin):
    list_display = ("get_name", "get_content", "get_class", "author", "direction", "publishdate", 'get_response')
    list_filter = ("direction", "responded")
    search_fields = ("name", )

    def get_name(self, obj):
        return u'<a href="/message/%s">%s</a>' % (obj.id, obj.name)

    get_name.short_description = 'Name'
    get_name.allow_tags = True

    def get_content(self, obj):
        return '<a href="/message_response/%s" target="_blank">%s</a>' % (obj.id, obj.content)

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
            return '<a href="/message_response/%s" target="_blank">Respond</a>' % obj.id

    get_response.short_description = 'Response Sent'
    get_response.allow_tags = True


class SmsAdmin(SummernoteModelAdmin):
    list_display = ("id", "msisdn", "date_sent", "message", "get_response")
    search_fields = ("msisdn", "date_sent", "message")
    list_filter = ("responded",)

    def get_response(self, obj):
        if obj.responded:
            return obj.respond_date
        else:
            return '<a href="/sms_response/%s">Respond</a>' % obj.id

    get_response.short_description = 'Response Sent'
    get_response.allow_tags = True


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
    list_filter = (UserFilter, 'question')
    search_fields = ("fix", "issue")

    def get_name(self, obj):
        return u'%s %s' % (obj.user.first_name, obj.user.last_name)
    get_name.short_description = "Name"

    def get_issue(self, obj):
        if obj.response is None:
            return obj.issue
        else:
            return u'<a href="/report_response/%s" target="_blank">%s</a>' % (obj.id, obj.issue)
    get_issue.allow_tags = True
    get_issue.short_description = "What is wrong with this question?"

    def get_fix(self, obj):
        if obj.response is None:
            return obj.fix
        else:
            return u'<a href="/report_response/%s" target="_blank">%s</a>' % (obj.id, obj.fix)
    get_fix.allow_tags = True
    get_fix.short_description = "How can we fix the problem?"

    def get_question(self, obj):
        return u'<p>%s</p><a href="/preview/%s" taget="_blank">View Question</a>' % (obj.question.name, obj.question.id)
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
            return u'<p>None</p><a href="/report_response/%s" target="_blank">Respond</a>' % obj.id
        else:
            return obj.response.publish_date
    get_response.allow_tags = True
    get_response.short_description = "Response Sent"


class ReportResponseAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date', 'content')
    search_fields = ['publish_date', 'title', 'content']


class SmsQueuedAdmin(admin.ModelAdmin):
    list_display = ('get_send_date', 'msisdn', 'message', 'sent')
    list_filter = ('sent',)
    search_fields = ('msisdn', 'message', 'send_date')

    def get_send_date(self, obj):
        return u'<a href="/smsqueue/%s/">%s</a>' % (obj.id, obj.send_date)
    get_send_date.short_description = 'Time Sms will be send'
    get_send_date.allow_tags = True

    actions = ['mark_as_sent']

    def mark_as_sent(modeladmin, request, queryset):
        queryset.update(sent=True, sent_date=datetime.now())

    mark_as_sent.short_description = 'Mark as sent'


class ModerationAdmin(admin.ModelAdmin):
    list_display = (
        'get_content',
        'get_comment',
        'get_author',
        'get_reply',
        'get_publishdate',
        'get_published',
        'get_unmoderated_by',
        'get_unmoderated_date',
        'get_ban'
    )

    list_filter = (
        ModerationContentFilter,
        ModerationUserFilter,
        ModerationContentTypeFilter,
        ModerationStateFilter
    )

    def get_content(self, obj):
        if obj.description:
            url = ".?content=%s" % urlquote(obj.description)
            return '<a href="%s" target="_blank">%s</a>' % (url, obj.description)
        else:
            return ''

    get_content.short_description = 'Content'
    get_content.allow_tags = True

    def get_comment(self, obj):
        url_base = "/admin/communication/"
        if obj.type == 1:
            url = url_base + "postcomment/%s" % obj.mod_id
        elif obj.type == 2:
            url = url_base + "discussion/%s" % obj.mod_id
        elif obj.type == 3:
            url = url_base + "chatmessage/%s" % obj.mod_id
        else:
            url = ''

        return '<a href="%s" target="_blank">%s</a>' % (url, obj.content)

    get_comment.short_description = 'Comment'
    get_comment.allow_tags = True

    def get_author(self, obj):
        if obj.author:
            url = ".?user=%d" % obj.author.id
            return '<a href="%s" target="_blank">%s</a>' % (url, obj.author.get_display_name())
        else:
            return obj.author

    get_author.short_description = 'User'
    get_author.allow_tags = True

    def get_reply(self, obj):
        if obj.response is None or len(obj.response.strip()) == 0:
            if obj.type == Moderation.MT_BLOG_COMMENT:
                url = "/blog_comment_response/%d" % obj.mod_id
                retval = '<a href="%s" target="_blank">Add Reply</a>' % url
            elif obj.type == Moderation.MT_DISCUSSION:
                url = '/discussion_response/%d' % obj.mod_id
                retval = '<a href="%s" target="_blank">Add Reply</a>' % url
            elif obj.type == Moderation.MT_CHAT:
                url = "/chat_response/%d" % obj.mod_id
                retval = '<a href="%s" target="_blank">Add Reply</a>' % url
            else:
                retval = 'Add Reply'

            return retval
        elif obj.original_content and len(obj.original_content.strip()) > 0:
            # Comment has been removed
            return obj.content
        else:
            return obj.response

    get_reply.short_description = 'Reply'
    get_reply.allow_tags = True

    def get_publishdate(self, obj):
        return obj.publishdate

    get_publishdate.short_description = 'Created on'
    get_publishdate.allow_tags = True

    def get_published(self, obj):
        url_base = '/admin/communication/'
        if obj.type == Moderation.MT_BLOG_COMMENT:
            url_part = 'postcomment'
        elif obj.type == Moderation.MT_DISCUSSION:
            url_part = 'discussion'
        elif obj.type == Moderation.MT_CHAT:
            url_part = 'chatmessage'

        if obj.moderated:
            return '<p>Published</p><a href="%s%s/unpublish/%d" target="_blank" ' \
                   'onclick="setTimeout(function(){window.location = window.location.href;}, 1000)">Unpublish</a>' % \
                   (url_base, url_part, obj.mod_id)
        elif obj.moderated is False and obj.unmoderated_date is not None:
            return '<p>Unpublished</p><a href="%s%s/publish/%d" target="_blank" ' \
                   'onclick="setTimeout(function(){window.location = window.location.href;}, 1000)">Publish</a>' % \
                   (url_base, url_part, obj.mod_id)
        else:
            return '<a href="%s%s/publish/%d" target="_blank" ' \
                   'onclick="setTimeout(function(){window.location = window.location.href;}, 1000)">Publish</a>' % \
                   (url_base, url_part, obj.mod_id)

    get_published.short_description = 'Published'
    get_published.allow_tags = True

    def get_unmoderated_by(self, obj):
        if obj.unmoderated_by:
            return obj.unmoderated_by.get_display_name()
        else:
            return ''

    get_unmoderated_by.short_description = 'Unpublished by'
    get_unmoderated_by.allow_tags = True

    def get_unmoderated_date(self, obj):
        if obj.unmoderated_date:
            return obj.unmoderated_date
        else:
            return ''

    get_unmoderated_date.short_description = 'Unpublished on'
    get_unmoderated_date.allow_tags = True

    def get_ban(self, obj):
        bans = get_user_bans(obj.author)

        if bans.count() == 0:
            return ''
        else:
            dur = bans[0].get_duration()
            plural = ''

            if dur > 1:
                plural = 's'

            return '%d day%s' % (dur, plural)

    get_ban.short_description = 'Ban'
    get_ban.allow_tags = True

    actions = ['reply_to_selected', 'unpublish_selected', 'publish_selected']

    def reply_to_selected(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        cnt1 = queryset.filter(mod_pk__in=selected, type=Moderation.MT_BLOG_COMMENT).count()
        cnt2 = queryset.filter(mod_pk__in=selected, type=Moderation.MT_DISCUSSION).count()
        cnt3 = queryset.filter(mod_pk__in=selected, type=Moderation.MT_CHAT).count()

        if (cnt1 > 0 and (cnt2 + cnt3) != 0) or (cnt2 > 0 and (cnt1 + cnt3) != 0) or (cnt3 > 0 and (cnt1 + cnt2) != 0):
            return HttpResponse("Plesse select only messages of the same type when doing a bulk reply")

        if cnt1 > 0:
            atype = Moderation.MT_BLOG_COMMENT
            url = "blog_comment_response_selected"
        elif cnt2 > 0:
            atype = Moderation.MT_DISCUSSION
            url = "discussion_response_selected"
        elif cnt3 > 0:
            atype = Moderation.MT_CHAT
            url = "chat_response_selected"

        qs = list(str(row['mod_id']) for row in queryset.filter(mod_pk__in=selected, type=atype).values('mod_id'))
        return HttpResponseRedirect('/%s/%s' % (url, ",".join(qs)))

    reply_to_selected.short_description = 'Add reply'

    def unpublish_selected(modeladmin, request, queryset):
        blogcomments = queryset.filter(type=Moderation.MT_BLOG_COMMENT).values("mod_id")
        discusions = queryset.filter(type=Moderation.MT_DISCUSSION).values("mod_id")
        chats = queryset.filter(type=Moderation.MT_CHAT).values("mod_id")

        PostComment.objects.filter(id__in=blogcomments).update(
            moderated=False,
            unmoderated_date=datetime.now(),
            unmoderated_by=request.user
        )
        Discussion.objects.filter(id__in=discusions).update(
            moderated=False,
            unmoderated_date=datetime.now(),
            unmoderated_by=request.user
        )
        ChatMessage.objects.filter(id__in=chats).update(
            moderated=False,
            unmoderated_date=datetime.now(),
            unmoderated_by=request.user
        )

    unpublish_selected.short_description = 'Unpublish'

    def publish_selected(modeladmin, request, queryset):
        blogcomments = queryset.filter(type=Moderation.MT_BLOG_COMMENT).values("mod_id")
        discusions = queryset.filter(type=Moderation.MT_DISCUSSION).values("mod_id")
        chats = queryset.filter(type=Moderation.MT_CHAT).values("mod_id")

        PostComment.objects.filter(id__in=blogcomments).update(moderated=True)
        Discussion.objects.filter(id__in=discusions).update(moderated=True)
        ChatMessage.objects.filter(id__in=chats).update(moderated=True)

    publish_selected.short_description = 'Publish'

    def get_actions(self, request):
        #Disable delete
        actions = super(ModerationAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


class BanAdmin(admin.ModelAdmin):
    list_display = ('banned_user', 'banning_user', 'when', 'till_when', 'source_type', 'source_pk')
    list_filter = (
        BannedUserFilter,
        BanningUserFilter,
    )
    ordering = ('-till_when',)


class PostCommentAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'post',
        'content',
        'publishdate',
        'moderated',
        'unmoderated_date',
        'unmoderated_by',
        'original_content'
    )

    fieldsets = [
        ("Content",
            {"fields": ["post", "content", "author", "publishdate", "moderated"]}),
        ("Moderation",
            {"fields": ["original_content", "unmoderated_date", "unmoderated_by"]}),
    ]


# Communication
admin.site.register(Sms, SmsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(PostComment, PostCommentAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatGroup, ChatGroupAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(Discussion, DiscussionAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportResponse, ReportResponseAdmin)
admin.site.register(SmsQueue, SmsQueuedAdmin)
admin.site.register(Moderation, ModerationAdmin)
admin.site.register(Ban, BanAdmin)