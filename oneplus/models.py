from django.db import models
from content.models import TestingQuestion
from core.models import Participant, ParticipantQuestionAnswer
from datetime import datetime, timedelta, time
from random import randint
from content.models import GoldenEgg, EventQuestionAnswer
from organisation.models import CourseModuleRel


# Participant(Learner) State
class LearnerState(models.Model):
    participant = models.ForeignKey(Participant, null=True, blank=False)
    active_question = models.ForeignKey(
        TestingQuestion,
        null=True,
        blank=False
    )
    active_result = models.NullBooleanField()
    golden_egg_question = models.PositiveIntegerField(default=0)
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
        return [start, end]

    def get_number_questions(self, answered_count, week_day):
        required_count = (week_day + 1) * self.QUESTIONS_PER_DAY
        return required_count - answered_count

    def is_weekend(self, week_day):
        return week_day == self.SATURDAY or week_day == self.SUNDAY

    def get_week_day(self):
        week_day = self.today().weekday()
        if self.is_training_weekend():
            return self.MONDAY
        elif self.is_weekend(week_day):
            return self.FRIDAY
        return week_day

    def get_num_questions_answered_today(self):
        # Get list of answered questions for this week
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
            answerdate__gte=self.today(),
            answerdate__lte=self.today() + timedelta(days=1)).count()

    def get_answers_this_week(self):
        # Get list of answered questions for this week, excluding today
        return ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
            answerdate__range=self.get_week_range(),
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

        if self.is_training_week():
            answer += len(self.get_training_questions())

        return answer

    def check_monday_after_training(self, total_answered):
        week_day = self.today().weekday()
        return week_day == self.MONDAY \
               and total_answered <= self.QUESTIONS_PER_DAY

    def get_training_questions(self):
        answered = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct().order_by('answerdate')
        training_questions = []

        for x in answered:
            if self.is_training_date(x.answerdate):
                training_questions.append(x)
            else:
                break

        return training_questions

    def is_training_week(self):
        # Get week day
        weekday = self.participant.datejoined.weekday()

        # Get monday after training week
        two_weeks = 14
        days = 0 - weekday + two_weeks
        next_monday = self.participant.datejoined + timedelta(days=days)

        # If it is before the monday after training week
        if self.today().date() < next_monday.date():
            return True
        else:
            return False

    def get_monday_after_training(self):
        # Get week day
        weekday = self.participant.datejoined.weekday()
        one_week = 7
        days = 0 - weekday + one_week

        # Get monday after training week
        return self.participant.datejoined + timedelta(days=days)

    def is_training_date(self, date):
        weekday = date.weekday()
        if not self.is_weekend(weekday):
            return False

        next_monday = self.get_monday_after_training()
        if date < next_monday:
            return True
        else:
            return False

    def is_training_weekend(self):
        return self.is_training_date(self.today())

    def get_total_questions(self):
        answered_this_week = self.get_answers_this_week()
        num_answered_this_week = len(answered_this_week)
        training_questions = self.get_training_questions()

        # If it is a training week, then add on the training question
        if self.is_training_week() and not self.is_training_weekend():
            num_answered_this_week += len(training_questions)

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
