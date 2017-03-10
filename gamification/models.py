from django.db import models
from organisation.models import Course, Module
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class GamificationPointBonus(models.Model):

    """
    BadgeTemplates can be specified and linked to a Course and Scenario.
    A BadgeTemplate has a name, an image (jpg, png, gif) and a description.
    Badges are instances of a BadgeTemplate awarded to a specific user.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    image = models.ImageField("Image", upload_to="img/", blank=True, null=True)
    value = models.PositiveIntegerField("Value", null=True, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Point Bonus"
        verbose_name_plural = "Point Bonuses"


@python_2_unicode_compatible
class GamificationBadgeTemplate(models.Model):

    """
    PointBonuses are also linked to a Course and Scenario and award the
    user extra points for achieving a specific scenario. A PointBonus has
    a name, an image (jpg, png, gif), a description and the number of
    points to be awarding.
    """
    description = models.CharField("Description", max_length=500, blank=True)
    image = models.ImageField("Image", upload_to="img/", blank=True, null=True)
    is_active = models.BooleanField("is active", default=False)
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    order = models.IntegerField("Order Number", blank=True, null=True)

    def __str__(self):
        return self.name

    def image_(self):
        return '<a href="/media/{0}"><img src="/media/{0}"></a>'.format(
            self.image)
    image_.allow_tags = True

    class Meta:
        verbose_name = "Badge Template"
        verbose_name_plural = "Badge Templates"


@python_2_unicode_compatible
class GamificationScenario(models.Model):
    ONCE = 1
    MULTIPLE = 2

    AWARD_TYPE_CHOICES = (
        (ONCE, "Once"),
        (MULTIPLE, "Multiple")
    )

    """
    Gamification is one of the hardest problems to solve elegantly on this
    platform. We want to be able to hand out extra points and badges based
    on specific conditions (scenarios) being met by the user.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    event = models.CharField("Event", max_length=500, blank=True)
    course = models.ForeignKey(Course, null=True, blank=True)
    module = models.ForeignKey(Module, null=True, blank=True)
    point = models.ForeignKey(GamificationPointBonus, null=True, blank=True)
    badge = models.ForeignKey(GamificationBadgeTemplate, null=True, blank=True)
    award_type = models.PositiveIntegerField("Times awarded", choices=AWARD_TYPE_CHOICES, default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"
