from datetime import datetime
import operator

from djcelery import celery
from content.forms import render_mathml
from content.models import Event, EventParticipantRel, EventQuestionRel
from core.models import Participant
from organisation.models import CourseModuleRel


@celery.task
def render_mathml_content():
    render_mathml()


@celery.task
def end_event_processing():
    events = Event.objects.filter(deactivation_date__gt=datetime.now(), end_processed=False)
    for event in events:
        participants = EventParticipantRel.objects.filter(event=event)

        scores = {}
        for participant in participants:
            scores[participant.id] = EventQuestionRel.objects.filter(event=event, participant=participant, correct=True) \
                .count()
        scores = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

        winner_ids = [scores[0][0]]
        index = 0
        while scores[index][1] == scores[index + 1][1]:
            winner_ids.append(scores[index + 1][0])
            index += 1
        winners = Participant.objects.filter(id__in=winner_ids)

        module = CourseModuleRel.objects.filter(course=event.course).first()
        if "spot test" in event.name.lowercase():
            for winner in winners:
                winner.award_scenario("SPOT_TEST_CHAMP", module)
        elif "exam" in event.name.lowercase():
            for winner in winners:
                winner.award_scenario("EXAM_CHAMP", module)
        event.end_processed = True
        event.save()
