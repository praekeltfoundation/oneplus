from django.db import models


# An organisations is a container for schools.
# This exists almost solely for situations where MobileU is deployed as a SAAS with multiple organisations on a single
# server.
class Organisation(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)
    #schools

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"


# Schools have a name, description and some basic contact details. A school manager has the ability to CRUD courses
# under a school.
class School(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, blank=False)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"


# Courses have a name, description and slug. A courses manager has the ability to CRUD courses content (Modules,
# Pages & Posts etc). Courses additionally have a series of settings which define the 'business logic' for a courses.
class Course(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    slug = models.SlugField("Slug", blank=True)
    #modulees
    #pages
    #posts
    #settings

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"


# Modules have a name, description, learning content, testing content and gamification logic.
class Module(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    #learning
    #testing
    #gamification

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"