from django.db import models
from django.core.validators import MaxValueValidator
from organisation.models import Module
from django.core.urlresolvers import reverse
from django.utils.html import remove_tags
import bleach
from mobileu.utils import format_width, align


class LearningChapter(models.Model):

    """
    Each modules has learning content which can be broken up into chapters.
    Essentially this content is HTML and needs to
    be able to include images, videos, audio clips and hyperlinks to
    external resources. The management interface will
    only expose limited formatting options.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    content = models.TextField("Content", blank=True)

    def save(self, *args, **kwargs):
        self.content = bleach.clean(self.content,
                                    allowed_tags,
                                    allowed_attributes,
                                    allowed_styles,
                                    strip=True)
        self.content = format_width(self.content)
        self.content = align(self.content)
        super(LearningChapter, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Learning Chapter"
        verbose_name_plural = "Learning Chapters"


class TestingBank(models.Model):

    """
    Each modules has a series of questions. The MVP supports two question
    types, multiple-choice and free-form entry.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    question_order = models.PositiveIntegerField("Question Order", choices=(
        (1, "Random"), (2, "Ordered"), (3, "Random Intelligent")), default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Test Bank"
        verbose_name_plural = "Test Banks"


class TestingQuestion(models.Model):
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    question_content = models.TextField("Question", blank=True)
    answer_content = models.TextField("Answer", blank=True)
    difficulty = models.PositiveIntegerField(
        "Difficulty", choices=(
            (1, "Not Specified"),
            (2, "Easy"),
            (3, "Normal"),
            (4, "Advanced")
        ),
        default=1)
    points = models.PositiveIntegerField(
        "Points",
        validators=[MaxValueValidator(500)],
        default=1,
        blank=False,
    )

    textbook_link = models.CharField(
        "Textbook Link",
        max_length=500,
        blank=True,
        null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.question_content = bleach.clean(self.question_content,
                                             allowed_tags,
                                             allowed_attributes,
                                             allowed_styles,
                                             strip=True)
        self.answer_content = bleach.clean(self.answer_content,
                                           allowed_tags,
                                           allowed_attributes,
                                           allowed_styles,
                                           strip=True)
        self.question_content = format_width(self.question_content)
        self.question_content = align(self.question_content)
        self.answer_content = format_width(self.answer_content)
        self.answer_content = align(self.answer_content)

        super(TestingQuestion, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Test Question"
        verbose_name_plural = "Test Questions"


class TestingQuestionOption(models.Model):
    name = models.CharField(
        "Name",
        max_length=500,
        null=True,
        blank=False,
        unique=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    order = models.PositiveIntegerField("Order", default=1)
    content = models.TextField("Content", blank=True)
    correct = models.BooleanField("Correct")

    def save(self, *args, **kwargs):
        self.content = bleach.clean(self.content,
                                    allowed_tags,
                                    allowed_attributes,
                                    allowed_styles,
                                    strip=True)
        self.content = format_width(self.content)
        self.content = align(self.content)
        super(TestingQuestionOption, self).save(*args, **kwargs)

    def link(self):
        return "<a href='%s' target='_blank'>Edit</a>" % reverse(
            'admin:content_testingquestionoption_change',
            args=[
                self.id])
    link.allow_tags = True

    def admin_thumbnail(self):
        thumbnail = remove_tags(self.content, "p br")
        return u'%s' % thumbnail
    admin_thumbnail.short_description = 'Content'
    admin_thumbnail.allow_tags = True

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"

allowed_tags = ['b', 'i', 'strong', 'em', 'img', 'a', 'br']
allowed_attributes = ['href', 'title', 'style', 'src']
allowed_styles = [
    'font-family',
    'font-weight',
    'text-decoration',
    'font-variant',
    'width',
    'height']
