from django.db import models
from core.models import *
from django.db.models.query import Q
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
            _questionstochoosefrom = TestingQuestion.objects.filter(bank__module__course=self.participant.classs.course)
            _idx = random.randrange(0, _questionstochoosefrom.count()-1)
            self.active_question = _questionstochoosefrom[_idx]
            self.active_result = None
            self.save()

        return self.active_question