from django.db import models
from django.core.validators import MaxValueValidator

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


# Classes link Users (learners, mentors, etc) and Courses. A user has to be in a class to participate in a modules.
class Class(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    type = models.PositiveIntegerField("Type", choices=(
        (1, "Traditional"), (2, "Open Class ")), default=1)
    startdate = models.DateField("Start Date", null=True, blank=True)
    enddate = models.DateField("End Date", null=True, blank=True)
    #learners
    #mentors
    #managers

    def __str__(self):
        return self.name


# Each modules has learning content which can be broken up into chapters. Essentially this content is HTML and needs to
# be able to include images, videos, audio clips and hyperlinks to external resources. The management interface will
# only expose limited formatting options.
class LearningChapter(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    content = models.TextField("Content", blank=True)

    def __str__(self):
        return self.name


# Each modules has a series of questions. The MVP supports two question types, multiple-choice and free-form entry.
class TestingBank(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    question_order = models.PositiveIntegerField("Question Order", choices=(
        (1, "Random"), (2, "Ordered"), (3, "Random Intelligent")), default=1)

    def __str__(self):
        return self.name


class TestingQuestion(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    bank = models.ForeignKey(TestingBank, null=True, blank=False)
    question_content = models.TextField("Question", blank=True)
    answer_content = models.TextField("Answer", blank=True)
    difficulty = models.PositiveIntegerField("Difficulty", choices=(
        (1, "Not Specified"), (2, "Easy"), (3, "Normal"), (4, "Advanced")), default=1)
    points = models.PositiveIntegerField("Points", validators=[MaxValueValidator(50)], default=0)

    def __str__(self):
        return self.name


class TestingQuestionOption(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    order = models.PositiveIntegerField("Order", default=1)
    content = models.TextField("Content", blank=True)
    correct = models.BooleanField("Correct")

    def __str__(self):
        return self.name


# BadgeTemplates can be specified and linked to a Course and Scenario. A BadgeTemplate has a name, an image (jpg, png,
# gif) and a description. Badges are instances of a BadgeTemplate awarded to a specific user.
class GamificationPointBonus(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    image = models.URLField("Image", null=True, blank=False)
    value = models.PositiveIntegerField("Value", null=True, blank=False)

    def __str__(self):
        return self.name


# PointBonuses are also linked to a Course and Scenario and award the user extra points for achieving a specific
# scenario. A PointBonus has a name, an image (jpg, png, gif), a description and the number of points to be awarding.
class GamificationBadgeTemplate(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    image = models.URLField("Image", null=True, blank=False)

    def __str__(self):
        return self.name

# Gamification is one of the hardest problems to solve elegantly on this platform. We want to be able to hand out extra
# points and badges based on specific conditions (scenarios) being met by the user.
class GamificationScenario(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    module = models.ForeignKey(Module, null=True, blank=False)
    event = models.CharField("Event", max_length=50, blank=True)
    point = models.ForeignKey(GamificationPointBonus, null=True, blank=True)
    badge = models.ForeignKey(GamificationBadgeTemplate, null=True, blank=True)

    def __str__(self):
        return self.name


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


# Courses can have blog posts which include HTML and images. These posts support basic non-threaded text-only
# commentary. A blog index page shows a paginated list of the blog posts available with the most recent at the top.
# 10 posts per page with a blurb and click through to read more.
class Post(models.Model):
    name = models.CharField("Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


class Learner(models.Model):
    firstname = models.CharField("FirstName", max_length=50, null=True, blank=False, unique=True)
    lastname = models.CharField("LastName", max_length=50, null=True, blank=False, unique=True)
    username = models.CharField("UserName", max_length=50, null=True, blank=False, unique=True)
    password = models.CharField("Password", max_length=50, null=True, blank=False, unique=True)
    school = models.ForeignKey(School, null=True, blank=False)

    def name(self):
        return self.firstname + " " + self.lastname

    def __str__(self):
        return self.name()


# Connects a learner to a class. Indicating the learners total points earned as well as individual point and badges
# earned.
class Participant(models.Model):
    learner = models.ForeignKey(Learner, verbose_name="Learner")
    classs = models.ForeignKey(Class, verbose_name="Class")
    datejoined = models.DateField(verbose_name="Joined")
    points = models.PositiveIntegerField(verbose_name="Points Scored")
    pointbonus = models.ManyToManyField(GamificationPointBonus, verbose_name="Point Bonuses", blank=True)
    badgetemplate = models.ManyToManyField(GamificationBadgeTemplate, verbose_name="Badge Templates", blank=True)