from django.db import models
from django.conf import settings
from organisation.models import Course

# For the MVP phase of this project we will keep Pages and Posts very simplistic.
# The instance has a Landing page.
# Each instance has an About page.
# Each course has a Landing page.
# These pages are manageable in the administration interface.
class Page(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"


# Courses can have blog posts which include HTML and images. These posts support basic non-threaded text-only
# commentary. A blog index page shows a paginated list of the blog posts available with the most recent at the top.
# 10 posts per page with a blurb and click through to read more.
class Post(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateField("Publish Date", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"


# A minimal forum experience is available on
#   Each Course. This feature can be turned off at the school level.
#   Each Module. This feature can be turned off at the school level.
#   Each Question. This feature can be turned off at the school level.
# The forum experience in the MVP is very basic and does not support threading. Users are simply able to type a reply
# limited to 1000 characters. As with all other parts of the site, users' avatars are displayed next to their name as
# well as any special tags that show moderators etc.
# The MVP does not have any report abuse functionality.
class Discussion(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    content = models.TextField("Content", blank=True)
    #author = models.ForeignKey(settings.AUTH_USER_MODEL)
    publishdate = models.DateField("Publish Date", null=True, blank=True)
    moderated = models.NullBooleanField("Moderated", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"


class Message(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateField("Publish Date", null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    direction = models.PositiveIntegerField("Direction", choices=(
        (1, "Outgoing"), (2, "Incoming")), default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"


# Chat groups are Learner only places where messages can be exchanged.
class ChatGroup(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Chat Group"
        verbose_name_plural = "Chat Groups"


class ChatMessage(models.Model):
    chatgroup = models.ForeignKey(ChatGroup, null=True, blank=False)
    #learner = models.ForeignKey(Learner, null=True, blank=False)
    content = models.TextField("Content", blank=True)
    publishdate = models.DateField("Publish Date", null=True, blank=True)

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"