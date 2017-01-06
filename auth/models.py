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

    pass_reset_token = models.CharField(
        verbose_name="Password Reset Token",
        max_length=500,
        blank=True,
        null=True
    )

    pass_reset_token_expiry = models.DateTimeField(
        verbose_name="Password Reset Token Expiry",
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

    def generate_valid_reset_token(self):
        # Base 64 encode from random uuid bytes and make url safe
        self.pass_reset_token = ''.join(
            random.choice(
                string.ascii_letters +
                string.digits) for i in range(8))

        # Calculate expiry date
        self.pass_reset_token_expiry = datetime.now() + timedelta(hours=1)

    def generate_reset_password_token(self):
        # Check if reset password token needs regenerating
        if self.pass_reset_token_expiry is None \
                or timezone.now() > self.pass_reset_token_expiry:
            # Check uniqueness on generation
            self.generate_valid_reset_token()
            while CustomUser.objects.filter(
                    pass_reset_token=self.pass_reset_token).exists():
                self.generate_valid_reset_token()

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
    GR_10 = 'Grade 10'
    GR_11 = 'Grade 11'
    GR_12 = 'Grade 12'
    GR_GRAD = 'Graduate'

    grade_list = (GR_10, GR_11, GR_12, GR_GRAD)

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
        null=True,
        choices=((g, g) for g in grade_list)
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
    ENROLLED_CHOICES = (
        ("0", "Yes"),
        ("1", "No"))

    enrolled = models.PositiveIntegerField(
        verbose_name="Currently enrolled in ProMaths class?",
        blank=True,
        choices=ENROLLED_CHOICES,
        default=1)

    def get_class(self, active_only=False):
        part_set = self.participant_set.all()
        if active_only:
            part_set = part_set.filter(is_active=True)

        if part_set:
            classes = ", ".join([part.classs.name for part in part_set if part.classs and part.classs.name])

            return classes
        else:
            return None

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"


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
