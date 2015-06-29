from datetime import datetime
import operator

from djcelery import celery
from content.forms import render_mathml
from content.models import Event, EventParticipantRel, EventQuestionRel, EventQuestionAnswer
from core.models import Participant
from organisation.models import CourseModuleRel
from django.db.models import Count


@celery.task
def render_mathml_content():
    render_mathml()


@celery.task
def end_event_processing():
    events = Event.objects.filter(deactivation_date__gt=datetime.now(), end_processed=False)
    for event in events:
        scores = EventQuestionAnswer.objects.filter(event=event, correct=True).values("participant") \
            .order_by("-score").annotate(score=Count("pk"))

        winner_ids = [scores[0]["participant"]]
        index = 0
        while scores[index]["score"] == scores[index + 1]["score"]:
            winner_ids.append(scores[index + 1]["participant"])
            index += 1
        winners = Participant.objects.filter(id__in=winner_ids)

        module = CourseModuleRel.objects.filter(course=event.course).first()
        if event.type == 1:
            for winner in winners:
                winner.award_scenario("SPOT_TEST_CHAMP", module)
        elif event.type == 2:
            for winner in winners:
                winner.award_scenario("EXAM_CHAMP", module)
        event.end_processed = True
        event.save()
