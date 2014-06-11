from django.db import models
from django.contrib.auth.models import AbstractUser
from organisation.models import School, Course


# Base class for custom MobileU user model
class CustomUser(AbstractUser):
    mobile = models.CharField(verbose_name="Mobile Phone Number",
                              max_length=50, blank=False, unique=True)
    country = models.CharField(verbose_name="Country", max_length=50,
                               blank=False)
    area = models.CharField(verbose_name="Local Area", max_length=50,
                            blank=True)
    city = models.CharField(verbose_name="City", max_length=50, blank=True)
    optin_sms = models.BooleanField(verbose_name="Opt-In SMS Communications",
                                    default=False)
    optin_email = models.BooleanField(
        verbose_name="Opt-In Email Communications", default=False)

    def __str__(self):
        return self.username


# System administrator with access to the admin console
class SystemAdministrator(CustomUser):

    class Meta:
        verbose_name = "System Administrator"
        verbose_name_plural = "System Administrators"


# A manager of a school
class SchoolManager(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)

    class Meta:
        verbose_name = "School Manager"
        verbose_name_plural = "School Managers"


# A manager of a course
class CourseManager(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Manager"
        verbose_name_plural = "Course Managers"


# A mentor for a course
class CourseMentor(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Mentor"
        verbose_name_plural = "Course Mentors"


# A learner
class Learner(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"
