from itertools import chain
from django.db.models import Count, Sum
from organisation.models import School
from core.models import Participant


def get_class_leaderboard(_participant, max_uncollapsed):
    participant = _participant
    eligible_participants = Participant.objects.filter(classs=_participant.classs, is_active=True, points__gt=0)

    position = eligible_participants.filter(points__gt=_participant.points).count() + 1

    scores = eligible_participants\
        .values('points')\
        .annotate(num_participants=Count('id'))\
        .distinct()\
        .order_by('-points')[:10]

    leaderboard = []
    for score in scores:
        more = False
        if score['num_participants'] >= max_uncollapsed:
            more = True

        if participant.points == score['points']:
            p_me = eligible_participants.filter(id=participant.id)\
                .values('id', 'learner__first_name', 'learner__last_name')
            p_list = eligible_participants.filter(points=score['points'])\
                .values('id', 'learner__first_name', 'learner__last_name')[:max_uncollapsed - 1]
            p_list = p_me | p_list
        else:
            p_list = eligible_participants.filter(points=score['points'])\
                .values('id', 'learner__first_name', 'learner__last_name')[:max_uncollapsed]

        members = [{'me': (a['id'] == participant.id),
                    'name': "{0:s} {1:s}".format(a['learner__first_name'],
                                                 a['learner__last_name'])} for a in p_list]

        if len(members) > 0:
            members[0]['position'] = eligible_participants.filter(points__gt=score['points']).count() + 1

        leaderboard += [
            {'members': members,
             'points': score['points']}]

    return {'board': leaderboard, 'position': position, 'type': 'class'}


def get_school_leaderboard(_participant, max_uncollapsed):
    participant = _participant
    schools = School.objects.filter(learner__grade=_participant.learner.grade,
                                    learner__participant__is_active=True)\
        .values('id', 'name')\
        .distinct()\
        .annotate(points=Sum('learner__participant__points'))\
        .order_by('-points', 'name')

    my_school = schools.get(id=participant.learner.school.id)
    position = schools.filter(points__gt=my_school['points']).count() + 1

    scores = schools.filter(points__gt=0)\
        .values_list('points', flat=True)

    leaderboard = []
    for score in scores:
        more = False

        if my_school['points'] == score:
            p_me = schools.filter(id=participant.learner.school.id)\
                .values('id', 'name', 'points')
            p_list = schools.filter(points=score)\
                .exclude(id=participant.learner.school.id)\
                .values('id', 'name', 'points')\
                .order_by()[:max_uncollapsed - 1]
            p_list = list(chain(p_me, p_list))
        else:
            p_list = schools.filter(points=score)\
                .values('id', 'name', 'points')[:max_uncollapsed + 1]
            if p_list.count() >= max_uncollapsed:
                more = True
                p_list = p_list[:max_uncollapsed]

        members = [{'me': (a['id'] == participant.learner.school.id),
                    'name': a['name']} for a in p_list]

        if len(members) > 0:
            members[0]['position'] = schools.filter(points__gt=score).count() + 1

        leaderboard += [
            {'members': members,
             'points': score}]

    return {'board': leaderboard, 'position': position, 'type': 'school'}


def get_national_leaderboard(_participant, max_uncollapsed):
    participant = _participant
    eligible_participants = Participant.objects.filter(learner__grade=_participant.learner.grade,
                                                       is_active=True,
                                                       points__gt=0)

    position = eligible_participants.filter(points__gt=_participant.points).count() + 1

    scores = eligible_participants\
        .values('points')\
        .annotate(num_participants=Count('id'))\
        .distinct()\
        .order_by('-points')[:10]

    leaderboard = []
    for score in scores:
        more = False
        if score['num_participants'] >= max_uncollapsed:
            more = True

        if participant.points == score['points']:
            p_me = eligible_participants.filter(id=participant.id)\
                .values('id',
                        'learner__first_name',
                        'learner__last_name',
                        'learner__school__name')
            p_list = eligible_participants.filter(points=score['points'])\
                .values('id',
                        'learner__first_name',
                        'learner__last_name',
                        'learner__school__name')[:max_uncollapsed - 1]
            p_list = p_me | p_list
        else:
            p_list = eligible_participants.filter(points=score['points'])\
                .values('id', 'learner__first_name',
                        'learner__last_name',
                        'learner__school__name')[:max_uncollapsed]

        members = [{'me': (a['id'] == participant.id),
                    'name': "{0:s} {1:s}".format(a['learner__first_name'],
                                                 a['learner__last_name']),
                    'school': a['learner__school__name']} for a in p_list]

        if len(members) > 0:
            members[0]['position'] = eligible_participants.filter(points__gt=score['points']).count() + 1

        leaderboard += [
            {'members': members,
             'points': score['points']}]

    return {'board': leaderboard, 'position': position, 'type': 'national'}
