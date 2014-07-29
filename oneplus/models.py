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

    def today(self):
        return datetime.today()

    def get_week_range(self):
        today = self.today()
        start = today - timedelta(days=today.weekday())
        end = today - timedelta(days=1)  # Exclude current day
        return [start, end]

    def get_number_questions(self, answered_count, week_day):
        required_count = (week_day+1)*self.QUESTIONS_PER_DAY
        return required_count - answered_count

    def is_weekend(self, week_day):
        return week_day == self.SATURDAY or week_day == self.SUNDAY

    def get_week_day(self, total_answered_count):
        week_day = self.today().weekday()
        if self.is_weekend(week_day):
            if total_answered_count < self.QUESTIONS_PER_DAY:
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

    def get_all_answered(self):
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct().values_list('question')

    def get_questions_answered_week(self):
        return len(self.get_answered()) \
            + len(self.get_training_questions()) \
            + self.get_num_questions_answered_today()

    def check_monday_after_training(self, total_answered):
        week_day = self.today().weekday()
        return week_day == self.MONDAY \
            and total_answered <= self.QUESTIONS_PER_DAY

    def get_training_questions(self):
        answered = list(ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct().order_by('answerdate'))
        training_questions = []
        for x in answered:
            if self.is_weekend(x.answerdate.weekday()):
                training_questions.append(x)
            else:
                break

        return training_questions

    def is_training_weekend(self):
        # Get date joined
        date_joined = self.participant.learner.date_joined
        week_day = date_joined.weekday()
        monday_after_signup = date_joined + timedelta(days=7-week_day)

        # If today is less than the first monday after signup
        if self.today() < monday_after_signup.replace(tzinfo=None):
            return True
        else:
            return False

    def is_training_week(self):
        # Get date joined
        date_joined = self.participant.learner.date_joined

        week_day = date_joined.weekday()
        next_monday_after_signup = date_joined + timedelta(days=14-week_day)

        if self.today() < next_monday_after_signup.replace(tzinfo=None):
            return True
        else:
            return False

    def get_total_questions(self):
        answered_this_week = self.get_answered()
        num_answered_this_week = len(answered_this_week)
        answered_in_total = self.get_all_answered()
        training_questions = self.get_training_questions()

        # If it is a training week, then add on the training questions
        if self.is_training_week():

            num_answered_this_week += len(training_questions)

        # Get the day of the week - that saturday and sunday will mimic
        week_day = self.get_week_day(len(answered_in_total))
        total = self.get_number_questions(num_answered_this_week, week_day)
        return total

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

