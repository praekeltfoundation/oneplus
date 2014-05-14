from django.db import models
from organisation.models import Course
from auth.models import Learner
from gamification.models import GamificationPointBonus, GamificationBadgeTemplate
from content.models import TestingQuestion, TestingQuestionOption


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

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"


# Connects a learner to a class. Indicating the learners total points earned as well as individual point and badges
# earned.
class Participant(models.Model):
    learner = models.ForeignKey(Learner, verbose_name="Learner")
    classs = models.ForeignKey(Class, verbose_name="Class")
    datejoined = models.DateField(verbose_name="Joined")
    points = models.PositiveIntegerField(verbose_name="Points Scored")
    pointbonus = models.ManyToManyField(GamificationPointBonus, verbose_name="Point Bonuses", blank=True)
    badgetemplate = models.ManyToManyField(GamificationBadgeTemplate, verbose_name="Badge Templates", blank=True)

    def __str__(self):
        return self.learner.first_name

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"


class ParticipantQuestionAnswer(models.Model):
    participant = models.ForeignKey(Participant, verbose_name="Participant")
    question = models.ForeignKey(TestingQuestion, verbose_name="Question")
    option_selected = models.ForeignKey(TestingQuestionOption, verbose_name="Selected")
    correct = models.BooleanField("Correct")
    answerdate = models.DateField("Answer Date", null=True, blank=True)

    def __str__(self):
        return self.participant.learner.name

    class Meta:
        verbose_name = "Participant Question Response"
        verbose_name_plural = "Participant Question Responses"