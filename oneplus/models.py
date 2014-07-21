from django.db import models
from content.models import TestingQuestion
from core.models import Participant, ParticipantQuestionAnswer
from datetime import datetime, timedelta


# Participant(Learner) State
class LearnerState(models.Model):
    participant = models.ForeignKey(Participant, null=True, blank=False)
    active_question = models.ForeignKey(
        TestingQuestion,
        null=True,
        blank=False
    )
    active_result = models.NullBooleanField()
    QUESTIONS_PER_DAY = 3
    MONDAY = 0
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    # So can be overridden in tests.
    def today(self):
        return datetime.today()

    def get_week_range(self):
        today = self.today()
        start = today - timedelta(days=today.weekday())
        end = start - timedelta(days=1)
        return [start, end]

    def get_number_questions(self, answered, week_day):
        answered_count = len(answered)
        required_count = (week_day+1)*self.QUESTIONS_PER_DAY
        return required_count - answered_count

    def is_weekend(self, week_day):
        return week_day == self.SATURDAY or week_day == self.SUNDAY

    def get_week_day(self, answered_count):
        week_day = datetime.today().weekday()
        if self.is_weekend(week_day):
            if answered_count <= self.QUESTIONS_PER_DAY:
                return self.MONDAY
            else:
                return self.FRIDAY
        return week_day

    def get_num_questions_answered_today(self):
        # Get list of answered questions for this week
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
            answerdate=self.today()).count()

    def get_answered(self):
        # Get list of answered questions for this week
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
            answerdate__range=self.get_week_range(),
        ).distinct().values_list('question')

    def get_total_questions(self):
        # Get list of answered questions for this week
        answered = self.get_answered()

        # If weekend, calculate most appropriate day to mimic
        week_day = self.get_week_day(len(answered))
        return self.get_number_questions(answered, week_day)

    def getnextquestion(self):
        if self.active_question is None or self.active_result is not None:
            # Get list of answered questions
            answered = ParticipantQuestionAnswer.objects.filter(
                participant=self.participant
            ).distinct().values_list('question')

            # Get list of unanswered questions
            questions = TestingQuestion.objects.filter(
                bank__module__course=self.participant.classs.course
            ).exclude(id__in=answered)

            # If a question exists
            if questions.count() > 0:
                self.active_question = questions.order_by('?')[0]
                self.active_result = None
                self.save()

        return self.active_question

