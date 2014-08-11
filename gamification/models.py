from django.db import models
from organisation.models import Course, Module


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


class GamificationBadgeTemplate(models.Model):

    """
    PointBonuses are also linked to a Course and Scenario and award the
    user extra points for achieving a specific scenario. A PointBonus has
    a name, an image (jpg, png, gif), a description and the number of
    points to be awarding.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    image = models.ImageField("Image", upload_to="img/", blank=True, null=True)
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


class GamificationScenario(models.Model):

    """
    Gamification is one of the hardest problems to solve elegantly on this
    platform. We want to be able to hand out extra points and badges based
    on specific conditions (scenarios) being met by the user.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    event = models.CharField("Event", max_length=500, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    module = models.ForeignKey(Module, null=True, blank=True)
    point = models.ForeignKey(GamificationPointBonus, null=True, blank=True)
    badge = models.ForeignKey(GamificationBadgeTemplate, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"
