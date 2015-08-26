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
    end_event_processing_body()


# function to assist with testing
def today():
    return datetime.now()


def end_event_processing_body():
    # Only get exams and spot tests
    events = Event.objects.filter(
        deactivation_date__lt=today(),
        end_processed=False,
        type__in=[Event.ET_EXAM, Event.ET_SPOT_TEST]
    )

    scenarios = {
        Event.ET_SPOT_TEST: "SPOT_TEST_CHAMP",
        Event.ET_EXAM: "EXAM_CHAMP"
    }

    for event in events:
        scores = EventQuestionAnswer.objects.filter(event=event, correct=True).values("participant") \
            .order_by("-score").annotate(score=Count("pk"))
        if scores:
            winner_ids = [scores[0]["participant"]]
            index = 0
            score_size = len(scores)
            if score_size > 1:
                while index + 1 < score_size and scores[index]["score"] == scores[index + 1]["score"]:
                    winner_ids.append(scores[index + 1]["participant"])
                    index += 1

            winners = Participant.objects.filter(id__in=winner_ids)
            module = CourseModuleRel.objects.filter(course=event.course).first()

            for winner in winners:
                winner.award_scenario(scenarios[event.type], module, special_rule=True)
                EventParticipantRel.objects.filter(event=event, participant__id__in=winner_ids).update(winner=True)

        event.end_processed = True
        event.save()