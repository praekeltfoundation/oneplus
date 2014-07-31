from django.db import models
from django.conf import settings
from datetime import datetime
from organisation.models import Course, Module
from content.models import TestingQuestion


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
    moderated = models.NullBooleanField("Moderated", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"


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
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    moderated = models.BooleanField("Moderated", default=False)

    course = models.ForeignKey(Course, null=True, blank=True)
    module = models.ForeignKey(Module, null=True, blank=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=True)
    response = models.ForeignKey("self", null=True, blank=True)

    def __str__(self):
        return self.author.first_name + ": " + self.content

    class Meta:
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"


class Message(models.Model):
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=False)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    direction = models.PositiveIntegerField("Direction", choices=(
        (1, "Outgoing"), (2, "Incoming")), default=1)

    def __str__(self):
        return self.name

    @staticmethod
    def get_messages(user, course, limit):
        _msgs = Message.objects.filter(
            course=course, direction=1).order_by("publishdate").reverse()
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
        _msgs = Message.objects.filter(course=course, direction=1)
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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Chat Group"
        verbose_name_plural = "Chat Groups"


class ChatMessage(models.Model):
    chatgroup = models.ForeignKey(ChatGroup, null=True, blank=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateTimeField("Publish Date", null=True, blank=True)

    def __str__(self):
        return self.content

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

    class Meta:
        verbose_name = "Sms"
        verbose_name_plural = "Smses"
