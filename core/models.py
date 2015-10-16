from django.db import models
from django.db.models import Sum
from datetime import datetime
from organisation.models import Course
from organisation.models import PROVINCE_CHOICES
from auth.models import Learner, Teacher
from gamification.models import \
    GamificationPointBonus, GamificationBadgeTemplate, GamificationScenario
from content.models import TestingQuestion, TestingQuestionOption, EventParticipantRel, EventQuestionAnswer, \
    EventQuestionRel, GoldenEggRewardLog, Event
from django.db.models import Count


def today():
    return datetime.now()


class Class(models.Model):

    """
    Classes link Users (learners, mentors, etc) and Courses. A user has to
    be in a class to participate in a modules.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    type = models.PositiveIntegerField("Type", choices=(
        (1, "Traditional"), (2, "Open Class ")), default=1)
    startdate = models.DateTimeField("Start Date", null=True, blank=True)
    enddate = models.DateTimeField("End Date", null=True, blank=True)
    is_active = models.BooleanField("Is Active", default=True)
    province = models.CharField("Province", max_length=20, null=True, blank=True, choices=PROVINCE_CHOICES)
    # learners
    # mentors
    # managers

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"


class TeacherClass(models.Model):
    teacher = models.ForeignKey(Teacher)
    classs = models.ForeignKey(Class)


class Participant(models.Model):

    """
    Connects a learner to a class. Indicating the learners total points
    earned as well as individual point and badges earned.
    """
    learner = models.ForeignKey(Learner, verbose_name="Learner")
    classs = models.ForeignKey(Class, verbose_name="Class")
    datejoined = models.DateTimeField(verbose_name="Joined")
    points = models.PositiveIntegerField(verbose_name="Points Scored",
                                         default=0)

    # This will need to be removed but not until the data migration has occured
    pointbonus = models.ManyToManyField(
        GamificationPointBonus, through="ParticipantPointBonusRel",
        verbose_name="Point Bonuses", blank=True)
    badgetemplate = models.ManyToManyField(
        GamificationBadgeTemplate, through="ParticipantBadgeTemplateRel",
        verbose_name="Badge Templates", blank=True)
    is_active = models.BooleanField("Is Active", default=True)

    def __str__(self):
        return self.learner.first_name

    # Get the scenarios
    def get_scenarios(self, event, module, special_rule=False):
        scenarios = GamificationScenario.objects.filter(
            event=event,
            course=self.classs.course,
            module=module)

        if scenarios.count() > 0:
            return scenarios
        else:
            #Fall back to a default rule
            scenarios = GamificationScenario.objects.filter(
                event=event,
                course=self.classs.course,
                module=None
            )

            if scenarios.count() > 0:
                return scenarios
            else:
                if special_rule:
                    return GamificationScenario.objects.filter(
                        event=event,
                        course=None,
                        module=None
                    )
                else:
                    return scenarios

    def answer(self, question, option):
        # Create participant question answer
        answer = ParticipantQuestionAnswer(
            participant=self,
            question=question,
            option_selected=option,
            correct=option.correct,
            answerdate=today()
        )
        answer.save()

        # Award points to participant
        if option.correct:
            self.points += question.points
            self.save()

    def answer_event(self, event, question, option):
        #Create participant event question answer
        answer = EventQuestionAnswer(
            participant=self,
            event=event,
            question=question,
            question_option=option,
            correct=option.correct
        )
        answer.save()

        # Award points to participant if it's sumit
        if event.type == Event.ET_SUMIT and option.correct:
            self.points += question.points
            self.save()

    def answer_redo(self, question, option):
        # Create participant question answer
        answer = ParticipantRedoQuestionAnswer(
            participant=self,
            question=question,
            option_selected=option,
            correct=option.correct,
            answerdate=today()
        )
        answer.save()

    def can_take_event(self, event):
        event_participant_rel = EventParticipantRel.objects.filter(event=event, participant=self).first()

        if event_participant_rel:
            answered = EventQuestionAnswer.objects.filter(participant=self, event=event)\
                .aggregate(Count('question'))['question__count']
            total_questions = EventQuestionRel.objects.filter(event=event).\
                aggregate(Count('question'))['question__count']

            if event.type != 0:
                if event.number_sittings == 1 or event_participant_rel.results_received and answered >= total_questions:
                    return None, event_participant_rel
                else:
                    return True, event_participant_rel
            else:
                if answered <= 15:
                    return None, event_participant_rel
                else:
                    return True, event_participant_rel
        return True, None

    # # Probably to be used in migrations
    def recalculate_total_points(self):
        answers = ParticipantQuestionAnswer.objects.filter(
            participant=self,
            correct=True)
        sumit_answers = EventQuestionAnswer.objects.filter(
            event__type=Event.ET_SUMIT,
            participant=self,
            correct=True).exclude(event__event_points__isnull=True)
        events = EventParticipantRel.objects.filter(
            participant=self,
            results_received=True)
        badges = ParticipantBadgeTemplateRel.objects.filter(
            participant=self
        )
        golden_egg = GoldenEggRewardLog.objects.filter(participant=self).exclude(points__isnull=True)

        points = 0
        for answer in answers:
            points += answer.question.points
        for sumit_answer in sumit_answers:
                points += sumit_answer.question.points
        for event in events:
            if event.event.event_points:
                if event.event.type == Event.ET_SUMIT and event.winner is True:
                    points += event.event.event_points
                else:
                    points += event.event.event_points
        for badge in badges:
            if badge.scenario.point:
                points += badge.scenario.point.value
        for egg in golden_egg:
            points += egg.points

        self.points = points
        self.save()
        return points

    # Scenario's only apply to badges
    def award_scenario(self, event, module, special_rule=False):

        # Use scenarios for badges only
        scenarios = self.get_scenarios(event, module, special_rule=special_rule)

        for scenario in scenarios:
            # Badges may only be awarded once
            if scenario.badge is not None:
                template_rels = ParticipantBadgeTemplateRel.objects.filter(
                    participant=self, badgetemplate=scenario.badge)
                if not template_rels.exists():
                    b = ParticipantBadgeTemplateRel(
                        participant=self, badgetemplate=scenario.badge,
                        scenario=scenario, awarddate=today())
                    b.save()
                    if scenario.point:
                        ParticipantPointBonusRel(participant=self, scenario=scenario,
                                                 pointbonus=scenario.point, awarddate=today()).save()
                        # self.points += scenario.point.value
                    BadgeAwardLog(participant_badge_rel=b, award_date=today()).save()
                elif scenario.award_type == 2:
                    b = template_rels.first()
                    b.awardcount += 1
                    b.awarddate = today()
                    b.save()
                    if scenario.point:
                        ParticipantPointBonusRel(participant=self, scenario=scenario,
                                                 pointbonus=scenario.point, awarddate=today()).save()
                        # self.points += scenario.point.value
                    BadgeAwardLog(participant_badge_rel=b, award_date=today()).save()

        # Recalculate total points - not entirely sure that this should be here.
        self.points = self.recalculate_total_points()

        self.save()

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"


class ParticipantPointBonusRel(models.Model):
    participant = models.ForeignKey(Participant)
    pointbonus = models.ForeignKey(GamificationPointBonus)
    scenario = models.ForeignKey(GamificationScenario)
    awarddate = models.DateTimeField("Award Date", null=True, blank=True,
                                     default=today())


class ParticipantBadgeTemplateRel(models.Model):
    participant = models.ForeignKey(Participant)
    badgetemplate = models.ForeignKey(GamificationBadgeTemplate)
    scenario = models.ForeignKey(GamificationScenario)
    awarddate = models.DateTimeField(
        "Award Date", null=True, blank=False, default=today())
    awardcount = models.PositiveIntegerField(default=1)


class BadgeAwardLog(models.Model):
    participant_badge_rel = models.ForeignKey(ParticipantBadgeTemplateRel, blank=False, null=True)
    award_date = models.DateTimeField(auto_now_add=True)


class ParticipantQuestionAnswer(models.Model):
    participant = models.ForeignKey(Participant, verbose_name="Participant")
    question = models.ForeignKey(TestingQuestion, verbose_name="Question")
    option_selected = models.ForeignKey(
        TestingQuestionOption, verbose_name="Selected")
    correct = models.BooleanField("Correct", db_index=True)
    answerdate = models.DateTimeField(
        "Answer Date", null=True, blank=False, default=today(), db_index=True)

    def __str__(self):
        return self.participant.learner.username

    def delete(self):
        self.participant.recalculate_total_points()
        super(ParticipantQuestionAnswer, self).delete()

    class Meta:
        verbose_name = "Participant Question Response"
        verbose_name_plural = "Participant Question Responses"


class ParticipantRedoQuestionAnswer(models.Model):
    participant = models.ForeignKey(Participant, verbose_name="Participant")
    question = models.ForeignKey(TestingQuestion, verbose_name="Question")
    option_selected = models.ForeignKey(
        TestingQuestionOption, verbose_name="Selected")
    correct = models.BooleanField("Correct")
    answerdate = models.DateTimeField(
        "Answer Date", null=True, blank=False, default=today())

    def __str__(self):
        return self.participant.learner.username

    class Meta:
        verbose_name = "Participant Question Response"
        verbose_name_plural = "Participant Question Responses"


class Setting(models.Model):
    key = models.CharField("Key", max_length=50, blank=False, unique=True)
    value = models.TextField("Value", max_length=100, blank=False)

    @staticmethod
    def get_setting(key):
        setting = Setting.objects.filter(key__exact=key).first()

        if setting:
            return setting.value
        else:
            return None
