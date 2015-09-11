from django.db import models
from content.models import TestingQuestion
from core.models import Participant, ParticipantQuestionAnswer, ParticipantRedoQuestionAnswer
from datetime import datetime, timedelta, time
from random import randint
from content.models import GoldenEgg, EventQuestionAnswer, EventQuestionRel, SUMit
from organisation.models import CourseModuleRel


# Participant(Learner) State
class LearnerState(models.Model):
    participant = models.ForeignKey(Participant, null=True, blank=False)
    active_question = models.ForeignKey(
        TestingQuestion,
        null=True,
        blank=False,
        related_name="aquestion"
    )
    active_result = models.NullBooleanField()
    redo_question = models.ForeignKey(
        TestingQuestion,
        null=True,
        blank=False,
        related_name="rquestion",
    )
    active_redo_result = models.NullBooleanField()
    golden_egg_question = models.PositiveIntegerField(default=0)
    sumit_level = models.PositiveIntegerField(default=0)
    sumit_question = models.PositiveIntegerField(default=0)
    QUESTIONS_PER_DAY = 3
    MONDAY = 0
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def today(self):
        return datetime.combine(datetime.today().date(), time(0, 0))

    def get_week_range(self):
        today = self.today()
        start = today - timedelta(days=today.weekday())
        end = today
        return [start.date(), end.date()]

    def get_number_questions(self, answered_count, week_day):
        required_count = (week_day + 1) * self.QUESTIONS_PER_DAY
        return required_count - answered_count

    def is_weekend(self, week_day):
        return week_day == self.SATURDAY or week_day == self.SUNDAY

    def get_week_day(self):
        week_day = self.today().weekday()
        if self.is_weekend(week_day):
            return self.FRIDAY
        return week_day

    def get_num_questions_answered_today(self):
        # Get list of answered questions for today
        start = self.today().replace(hour=0, minute=0, second=0, microsecond=0)
        end = (start + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
            answerdate__gte=start,
            answerdate__lte=end).count()

    def get_answers_this_week(self):
        # Get list of answered questions for this week, excluding today
        if (self.sumit_level == 0):
            return ParticipantQuestionAnswer.objects.filter(
                participant=self.participant,
                answerdate__range=self.get_week_range(),
            ).distinct()
        else:
            _sumit = SUMit.objects.filter(course=self.participant.classs.course,
                                          activation_date__lte=datetime.now(),
                                          deactivation_date__gt=datetime.now()).first()
            return EventQuestionAnswer.objects.filter(participant=self.participant, event=_sumit,
                                                      answer_date__range=self.get_week_range(),
                                                      ).distinct()

    def get_unanswered(self):
        # Get list of answered questions
        answered = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct().values('question')

        # Get list of unanswered questions
        questions = TestingQuestion.objects.filter(
            module__in=self.participant.classs.course.modules.filter(type=1),
            module__is_active=True,
        ).exclude(id__in=answered)
        return questions

    def get_all_answered(self):
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct()

    def get_questions_answered_week(self):
        answer = len(self.get_answers_this_week()) \
            + self.get_num_questions_answered_today()

        return answer

    def get_total_questions(self):
        answered_this_week = self.get_answers_this_week()
        num_answered_this_week = len(answered_this_week)

        # Get the day of the week - that saturday and sunday will mimic
        week_day = self.get_week_day()
        total = self.get_number_questions(num_answered_this_week, week_day)
        return total

    def getnextquestion(self):
        golden_egg_list1 = GoldenEgg.objects.filter(classs=self.participant.classs,
                                                    course=self.participant.classs.course,
                                                    active=True)
        golden_egg_list2 = GoldenEgg.objects.filter(classs=None, course=self.participant.classs.course, active=True)
        if self.golden_egg_question == 0 and (golden_egg_list1.exists() or golden_egg_list2.exists()):
            self.golden_egg_question = randint(1, 15)

        if self.active_question is None or self.active_result is not None:
            questions = self.get_unanswered()

            # If a question exists
            if questions.count() > 0:
                self.active_question = questions.order_by('?')[0]
                self.active_result = None
                self.save()

        return self.active_question

    def get_next_redo_question(self):
        if self.redo_question is None or self.active_redo_result is not None:
            questions = self.get_redo_questions()
            if questions.count() > 0:
                self.redo_question = questions.order_by('?')[0]
                self.active_redo_result = None
                self.save()

        return self.redo_question

    def get_redo_questions(self):
        correct = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant, correct=True).distinct().values('question')
        redo_correct = ParticipantRedoQuestionAnswer.objects.filter(
            participant=self.participant, correct=True).distinct().values('question')
        answered = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant).distinct().values('question')

        return TestingQuestion.objects.filter(id__in=answered).exclude(id__in=correct).\
            exclude(id__in=redo_correct)
