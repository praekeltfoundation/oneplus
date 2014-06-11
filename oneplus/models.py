from django.db import models
from content.models import TestingQuestion
from core.models import *
from datetime import *
import random

# Participant(Learner) State
class LearnerState(models.Model):
    participant = models.ForeignKey(Participant, null=True, blank=False)
    active_question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    active_result = models.NullBooleanField()

    # If current question result has been achieved, assign next question randomly and return. Otherwise return current
    # question
    def getnextquestion(self):
        if self.active_question is None or self.active_result is not None:
            _answered = ParticipantQuestionAnswer.objects.filter(participant=self.participant,
                                                                 answerdate__gte=date.today()).distinct().values_list('question')
            _questionstochoosefrom = TestingQuestion.objects.filter(bank__module__course=self.participant.classs.course).exclude(id__in=_answered)
            _idx = random.randrange(0, _questionstochoosefrom.count())
            self.active_question = _questionstochoosefrom[_idx]
            self.active_result = None
            self.save()

        return self.active_question