from django.db import models
from content.models import TestingQuestion
from core.models import Participant, ParticipantQuestionAnswer, ParticipantRedoQuestionAnswer
from datetime import datetime, timedelta, time
from random import randint
from content.models import GoldenEgg, EventQuestionAnswer, SUMit


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

    def get_whole_week_range(self):
        today = self.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        return [start.date(), end.date()]

    def get_number_questions(self, answered_count, week_day):
        required_count = (week_day + 1) * self.QUESTIONS_PER_DAY
        return required_count - answered_count

    def get_questions_available_count(self):
        required_count = (self.get_week_day() + 1) * self.QUESTIONS_PER_DAY
        return required_count

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
        sumit = SUMit.objects.filter(course=self.participant.classs.course,
                                     activation_date__lte=datetime.now(),
                                     deactivation_date__gt=datetime.now()).first()

        if not sumit:
            return ParticipantQuestionAnswer.objects.filter(
                participant=self.participant,
                answerdate__range=self.get_week_range(),
            ).distinct()
        else:
            return EventQuestionAnswer.objects.filter(participant=self.participant, event=sumit,
                                                      answer_date__range=self.get_week_range(),
                                                      ).distinct()

    def get_correct_of_available(self):
        # Get list of answered questions for this week
        sumit = SUMit.objects.filter(course=self.participant.classs.course,
                                     activation_date__lte=datetime.now(),
                                     deactivation_date__gt=datetime.now()).first()

        if not sumit:
            num_correct = ParticipantQuestionAnswer.objects.filter(
                participant=self.participant,
                answerdate__range=self.get_whole_week_range(),
                correct=True,
            ).count()
        else:
            num_correct = EventQuestionAnswer.objects.filter(participant=self.participant, event=sumit,
                                                             answer_date__range=self.get_whole_week_range(),
                                                             correct=True,
                                                             ).count()

        num_available = self.get_questions_available_count()

        return num_correct, num_available

    def get_points_week(self):
        sumit = SUMit.objects.filter(course=self.participant.classs.course,
                                     activation_date__lte=datetime.now(),
                                     deactivation_date__gt=datetime.now()).first()

        if not sumit:
            points = ParticipantQuestionAnswer.objects.filter(
                participant=self.participant,
                answerdate__range=self.get_whole_week_range(),
                correct=True,
            ).aggregate(points=models.Sum('question__points'))
        else:
            points = EventQuestionAnswer.objects.filter(participant=self.participant, event=sumit,
                                                        answer_date__range=self.get_whole_week_range(),
                                                        correct=True,
                                                        ).aggregate(points=models.Sum('question__points'))
        return points["points"]

    def get_unanswered(self):
        # Get list of answered questions
        answered = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant,
        ).distinct().values('question')

        # Get list of unanswered questions
        questions = TestingQuestion.objects.filter(
            module__in=self.participant.classs.course.modules.filter(type=1),
            module__is_active=True,
            state=3
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
            else:
                self.redo_question = None
                self.save()

        return self.redo_question

    def get_redo_questions(self):
        wrong = ParticipantQuestionAnswer.objects.filter(participant=self.participant, correct=False).distinct()\
            .values_list('question__id', flat=True)

        redo_correct = ParticipantRedoQuestionAnswer.objects.filter(participant=self.participant, correct=True)\
            .distinct().values_list('question__id', flat=True)

        return TestingQuestion.objects.filter(id__in=wrong).exclude(id__in=redo_correct)

    def get_redo_question_count(self):
        wrong_count = ParticipantQuestionAnswer.objects.filter(participant=self.participant, correct=False)\
            .distinct()\
            .count()

        redo_correct_count = ParticipantRedoQuestionAnswer.objects.filter(participant=self.participant, correct=True)\
            .distinct()\
            .count()

        return redo_correct_count, wrong_count
