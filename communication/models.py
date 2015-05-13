from django.db import models
from django.conf import settings
from datetime import datetime
from organisation.models import Course, Module
from content.models import TestingQuestion
from django.db.models import Q
from django.utils.html import format_html, mark_safe


class Page(models.Model):

    """
    For the MVP phase of this project we will keep Pages and Posts very
    simplistic.
    The instance has a Landing page.
    Each instance has an About page.
    Each course has a Landing page.
    These pages are manageable in the administration interface.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"


class Post(models.Model):

    """
    Courses can have blog posts which include HTML and images. These posts
    support basic non-threaded text-only commentary. A blog index page
    shows a paginated list of the blog posts available with the most
    recent at the top. 10 posts per page with a blurb and click through
    to read more.
    """
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    big_image = models.ImageField(
        "Big Image", upload_to="img/", blank=True, null=True)
    small_image = models.ImageField(
        "Small Image", upload_to="img/", blank=True, null=True)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    moderated = models.NullBooleanField("Moderated", null=True, blank=True, default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"


class PostComment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="postcomment_user"
    )
    post = models.ForeignKey(Post, blank=False)
    content = models.TextField(blank=False)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    moderated = models.NullBooleanField("Moderated", null=True, blank=True, default=False)
    unmoderated_date = models.DateTimeField(null=True, blank=True)
    unmoderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="unmoderated_user"
    )
    original_content = models.TextField("Original Content", blank=True, null=True)


class Discussion(models.Model):

    """
    A minimal forum experience is available on
      Each Course. This feature can be turned off at the school level.
      Each Module. This feature can be turned off at the school level.
      Each Question. This feature can be turned off at the school level.
    The forum experience in the MVP is very basic and does not support
    threading. Users are simply able to type a reply limited to 1000
    characters. As with all other parts of the site, users' avatars are
    displayed next to their name as well as any special tags that show
    moderators etc. The MVP does not have any report abuse functionality.
    """
    name = models.CharField("Name", max_length=50, null=True, blank=True)
    description = models.CharField("Description", max_length=50, blank=True)
    content = models.TextField("Content", blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="discussion_author"
    )
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    moderated = models.BooleanField("Moderated", default=False)
    course = models.ForeignKey(Course, null=True, blank=True)
    module = models.ForeignKey(Module, null=True, blank=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=True)
    response = models.ForeignKey("self", null=True, blank=True)
    unmoderated_date = models.DateTimeField(null=True, blank=True)
    unmoderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="discussion_unmoderated_user"
    )
    original_content = models.TextField("Original Content", blank=True, null=True)

    def __unicode__(self):
        return self.author.first_name + ": " + self.content

    class Meta:
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"


class Message(models.Model):
    name = models.CharField(
        "Name",
        max_length=50,
        null=True,
        blank=False,
        unique=False
    )
    description = models.CharField(
        "Description",
        max_length=50,
        blank=True
    )
    course = models.ForeignKey(
        Course,
        null=True,
        blank=False,
        related_name='message_course'
    )
    to_class = models.ForeignKey(
        'core.Class',
        verbose_name="",
        null=True,
        blank=True
    )
    content = models.TextField(
        "Message",
        blank=True
    )
    publishdate = models.DateTimeField(
        "Publish Date",
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="message_author"
    )
    direction = models.PositiveIntegerField(
        "Direction",
        choices=(
            (1, "Outgoing"),
            (2, "Incoming")
        ),
        default=1
    )
    responded = models.BooleanField(
        default=False
    )
    responddate = models.DateTimeField(
        'Respond Date',
        null=True,
        blank=True
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="message_for_learner"
    )

    def __str__(self):
        return self.name

    @staticmethod
    def get_messages(user, course, limit):
        from core.models import Class

        _msgs_for_course = Q(
            course=course,
            direction=1,
            to_class__isnull=True
        )

        _classes = Class.objects.filter(course=course).values('id')

        _msgs_for_class = Q(
            course=course,
            direction=1,
            to_class__in=_classes,
            to_user__isnull=True
        )

        _msgs_for_user = Q(
            course=course,
            direction=1,
            to_class__in=_classes,
            to_user=user
        )

        _msgs = Message.objects.filter(_msgs_for_course | _msgs_for_class | _msgs_for_user).order_by("-publishdate")

        _result = list()
        for m in _msgs:
            _status = MessageStatus.objects.filter(
                message=m, user=user).first()
            if _status is None:
                m.viewed = False
                _result.append(m)
            elif not _status.hidden_status:
                m.viewed = _status.view_status
                _result.append(m)
        return _result[:limit]

    @staticmethod
    def unread_message_count(user, course):
        from core.models import Class

        _msgs_for_course = Q(
            course=course,
            direction=1,
            to_class__isnull=True
        )

        _classes = Class.objects.filter(course=course).values('id')

        _msgs_for_class = Q(
            course=course,
            direction=1,
            to_class__in=_classes,
            to_user__isnull=True
        )

        _msgs_for_user = Q(
            course=course,
            direction=1,
            to_class__in=_classes,
            to_user=user
        )

        _msgs = Message.objects.filter(_msgs_for_course | _msgs_for_class | _msgs_for_user)
        
        _counter = 0
        for m in _msgs:
            if not MessageStatus.objects.filter(
                    message=m, user=user, view_status=True).exists():
                _counter += 1
        return _counter

    def view_message(self, user):
        _status = MessageStatus.objects.filter(message=self, user=user).first()
        if _status is None:
            _status = MessageStatus(message=self, user=user)
        _status.view_status = True
        _status.view_date = datetime.now()
        _status.save()

    def hide_message(self, user):
        _status = MessageStatus.objects.filter(message=self, user=user).first()
        if _status is None:
            _status = MessageStatus(message=self, user=user)
        _status.hidden_status = True
        _status.hidden_date = datetime.now()
        _status.save()

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"


class MessageStatus(models.Model):

    """
    Message Status indicates if a user has viewed a message and if he has
    permanently hidden a message
    """
    message = models.ForeignKey(Message, null=True, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    view_status = models.BooleanField("View Status", default=False)
    view_date = models.DateTimeField("View Date", null=True, blank=True)
    hidden_status = models.BooleanField("Hidden Status", default=False)
    hidden_date = models.DateTimeField("Hidden Date", null=True, blank=True)

    def __str__(self):
        return self.message.name


class ChatGroup(models.Model):

    """
    Chat groups are Learner only places where messages can be exchanged.
    """
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Chat Group"
        verbose_name_plural = "Chat Groups"


class ChatMessage(models.Model):
    chatgroup = models.ForeignKey(ChatGroup, null=True, blank=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="chatmessage_author"
    )
    content = models.TextField("Content", blank=True)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    moderated = models.BooleanField("Moderated", default=False)
    unmoderated_date = models.DateTimeField(null=True, blank=True)
    unmoderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="chatmessage_unmoderated_user"
    )
    original_content = models.TextField("Original Content", blank=True, null=True)

    def __unicode__(self):
        return self.content

    def safe_content(self):
        return format_html(u"{0}", mark_safe(self.content))

    def safe_orig_content(self):
        return format_html(u"{0}", mark_safe(self.original_content))

    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"


# A sms
class Sms(models.Model):
    uuid = models.CharField(
        verbose_name="identifier",
        max_length=50,
        blank=False,
        null=True
    )
    message = models.TextField(
        verbose_name="Message",
        blank=False
    )
    date_sent = models.DateTimeField(
        verbose_name="Time Sms is sent",
        blank=False
    )
    msisdn = models.CharField(
        verbose_name="Mobile Phone Number",
        max_length=50,
        blank=True,
        null=True
    )
    responded = models.BooleanField(
        default=False,
        db_index=True,
        blank=True)
    respond_date = models.DateTimeField(
        verbose_name="Time sms was responded too",
        null=True,
        blank=True
    )
    response = models.ForeignKey(
        'SmsQueue',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Sms"
        verbose_name_plural = "Smses"


#ReportResponse
class ReportResponse(models.Model):
    title = models.CharField("Title", max_length=50, blank=False)
    publish_date = models.DateTimeField("Publish Date",
                                        blank=False, auto_now_add=True)
    content = models.TextField("Response Content", blank=False)

    class Meta:
        verbose_name = "Report Response"


#Reports
class Report(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=False)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    issue = models.TextField(blank=False)
    fix = models.TextField(blank=False)
    publish_date = models.DateTimeField("Publish Date", auto_now_add=True)
    response = models.ForeignKey(ReportResponse, null=True, blank=True)

    def create_response(self, _title, _content, _publish_date=datetime.now()):
        response = ReportResponse.objects.create(
            title=_title,
            content=_content,
            publish_date=_publish_date
        )

        self.response = response
        self.save()

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"


class SmsQueue(models.Model):
    message = models.TextField(
        verbose_name="Message",
        blank=False
    )
    send_date = models.DateTimeField(
        verbose_name="Time Sms will be sent",
        blank=False
    )
    msisdn = models.CharField(
        verbose_name="Mobile Phone Number",
        max_length=50,
        blank=True,
        null=True,
        db_index=True
    )
    sent = models.BooleanField(default=False, db_index=True)
    sent_date = models.DateTimeField(
        verbose_name="Time Sms was sent",
        blank=False,
        null=True,
        default=None
    )

    class Meta:
        verbose_name = "Queued Sms"
        verbose_name_plural = "Queued Smses"


class Moderation(models.Model):

    # pk for the view
    mod_pk = models.CharField(max_length=50, primary_key=True)
    # pk for the underlying model
    mod_id = models.PositiveIntegerField()
    type = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="moderation_author",
        on_delete=models.SET_NULL
    )
    moderated = models.BooleanField(default=False, blank=True)
    publishdate = models.DateTimeField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    unmoderated_date = models.DateTimeField(null=True, blank=True)
    unmoderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="moderation_unmoderator",
        on_delete=models.SET_NULL
    )
    original_content = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        return

    def delete(self, *args, **kwargs):
        return

    class Meta():
        managed = False
        db_table = 'view_communication_moderation'


class Profanity(models.Model):
    word = models.CharField(max_length=75, blank=False, null=False)
    translation = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Profanities"


class Ban(models.Model):
    source_types = (
        (1, 'Blog Comment'),
        (2, 'Discussion'),
        (3, 'Chat')
    )

    banned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        related_name='ban_banned_user'
    )
    banning_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        related_name='ban_banning_user'
    )
    when = models.DateTimeField(null=False, blank=False)
    till_when = models.DateTimeField(null=False, blank=False)
    source_type = models.PositiveIntegerField(
        null=False,
        blank=False,
        choices=source_types
    )
    source_pk = models.PositiveIntegerField(null=False, blank=False)

    def get_duration(self):
        diff = self.till_when - self.when

        if diff.seconds > 0:
            return diff.days + 1
        else:
            return diff.days