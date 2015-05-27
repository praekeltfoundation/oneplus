from django.db import models
from django.contrib.auth.models import AbstractUser
from organisation.models import School, Course
import random
import string
from datetime import datetime, timedelta
from communication.models import Sms
from django.utils import timezone
from communication.utils import get_user_bans
from django.db.models.signals import pre_delete
from django.dispatch import receiver


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

    unique_token = models.CharField(
        verbose_name="Unique Login Token",
        max_length=500,
        blank=True,
        null=True
    )

    unique_token_expiry = models.DateTimeField(
        verbose_name="Unique Login Token Expiry",
        null=True,
        blank=True
    )

    def generate_valid_token(self):
        # Base 64 encode from random uuid bytes and make url safe
        self.unique_token = ''.join(
            random.choice(
                string.ascii_letters +
                string.digits) for i in range(8))

        # Calculate expiry date
        self.unique_token_expiry = datetime.now() + timedelta(days=30)

    def generate_unique_token(self):
        # Check if unique token needs regenerating
        if self.unique_token_expiry is None \
                or timezone.now() > self.unique_token_expiry:
            # Check uniqueness on generation
            self.generate_valid_token()
            while CustomUser.objects.filter(
                    unique_token=self.unique_token).exists():
                self.generate_valid_token()

    def get_display_name(self):
        if self.first_name:
            temp = self.first_name + ' ' + self.last_name
        else:
            temp = self.username

        return temp

    def is_banned(self):
        cnt = get_user_bans(self).count()

        if cnt > 0:
            return True
        else:
            return False

    def __str__(self):
        return self.username


# System administrator with access to the admin console
class SystemAdministrator(CustomUser):

    class Meta:
        verbose_name = "System Administrator"
        verbose_name_plural = "System Administrators"

    def save(self, *args, **kwargs):
        self.is_staff = True
        self.is_superuser = True
        super(SystemAdministrator, self).save(*args, **kwargs)


# A manager of a school
class SchoolManager(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)

    class Meta:
        verbose_name = "School Manager"
        verbose_name_plural = "School Managers"

    def save(self, *args, **kwargs):
        self.is_staff = True
        super(SystemAdministrator, self).save(*args, **kwargs)


# A manager of a course
class CourseManager(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Manager"
        verbose_name_plural = "Course Managers"

    def save(self, *args, **kwargs):
        self.is_staff = True
        super(SystemAdministrator, self).save(*args, **kwargs)


# A mentor for a course
class CourseMentor(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Mentor"
        verbose_name_plural = "Course Mentors"


# A learner
class Learner(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)
    last_maths_result = models.FloatField(
        verbose_name="Last Terms Mathematics Result",
        blank=True,
        null=True
    )
    grade = models.CharField(
        verbose_name="User Grade",
        max_length=50,
        blank=True,
        null=True
    )
    welcome_message_sent = models.BooleanField(
        verbose_name="Welcome SMS Sent",
        blank=True,
        default=False
    )
    welcome_message = models.ForeignKey(
        Sms,
        null=True,
        blank=True
    )
    last_active_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners - Import/Export"


# A view of learner
class LearnerView(CustomUser):
    school = models.ForeignKey(
        School,
        null=True,
        blank=False,
        on_delete=models.SET_NULL
    )
    last_maths_result = models.FloatField(
        verbose_name="Last Terms Mathematics Result",
        blank=True,
        null=True
    )
    grade = models.CharField(
        verbose_name="User Grade",
        max_length=50,
        blank=True,
        null=True
    )
    welcome_message_sent = models.BooleanField(
        verbose_name="Welcome SMS Sent",
        blank=True,
        default=False
    )
    welcome_message = models.ForeignKey(
        Sms,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    last_active_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    questions_completed = models.IntegerField(
        verbose_name="Completed Questions",
        null=True,
        blank=True,
        default=0
    )
    questions_correct = models.IntegerField(
        verbose_name="Percentage Correct",
        null=True,
        blank=True,
        default=0,
    )

    def save(self, *args, **kwargs):
        if self.pk:
            lnr = Learner.objects.get(id=self.id)
        else:
            lnr = Learner()

        # abstract user fields
        lnr.username = self.username
        lnr.first_name = self.first_name
        lnr.last_name = self.last_name
        lnr.email = self.email
        lnr.is_staff = self.is_staff
        lnr.is_active = self.is_active

        # customer user fields
        lnr.mobile = self.mobile
        lnr.country = self.country
        lnr.area = self.area
        lnr.city = self.city
        lnr.optin_sms = self.optin_sms
        lnr.optin_email = self.optin_email
        lnr.unique_token = self.unique_token
        lnr.unique_token_expiry = self.unique_token_expiry

        # learner fields
        lnr.school = self.school
        lnr.last_maths_result = self.last_maths_result
        lnr.grade = self.grade
        lnr.welcome_message_sent = self.welcome_message_sent
        lnr.welcome_message = self.welcome_message
        lnr.last_active_date = self.last_active_date
        lnr.save()

        self.id = lnr.id
        self.pk = lnr.pk

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"
        managed = False
        db_table = "view_auth_learner"


#A teacher
class Teacher(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)
    welcome_message_sent = models.BooleanField(
        verbose_name="Welcome SMS Sent",
        blank=True,
        default=False
    )
    welcome_message = models.ForeignKey(
        Sms,
        null=True,
        blank=True
    )
    last_active_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
