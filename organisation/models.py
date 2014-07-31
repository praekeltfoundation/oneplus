from django.db import models


class Organisation(models.Model):

    """
    An organisations is a container for schools.
    This exists almost solely for situations where MobileU is deployed as
    a SAAS with multiple organisations on a single server.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)
    # schools

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"


class School(models.Model):

    """
    Schools have a name, description and some basic contact details.
    A school manager has the ability to CRUD courses under a school.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, blank=False)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"


class Course(models.Model):

    """
    Courses have a name, description and slug. A courses manager has the
    ability to CRUD courses content (Modules, Pages & Posts etc). Courses
    additionally have a series of settings which define the 'business
    logic' for a courses.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    slug = models.SlugField("Slug", blank=True)
    # modulees
    # pages
    # posts
    # settings

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"


class Module(models.Model):

    """
    Modules have a name, description, learning content, testing content
    and gamification logic.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    # learning
    # testing
    # gamification

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
