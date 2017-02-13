from __future__ import division
import logging

from django.conf import settings
from django.shortcuts import render
from auth.models import Learner
from core.models import Participant, ParticipantBadgeTemplateRel
from gamification.models import GamificationBadgeTemplate
from oneplus.auth_views import resolve_http_method
from oneplus.views import oneplus_check_user

logger = logging.getLogger(__name__)


@oneplus_check_user
def badges(request, state, user):
    def get():
        badge_id = request.GET.get('b', None)
        participant_id = request.GET.get('p', None)

        learner = None
        participant = None
        if participant_id and Participant.objects.filter(id=participant_id).exists():
            participant = Participant.objects.get(id=participant_id)
            learner = Learner.objects.get(participant__id=participant_id)
            if not learner.public_share:
                learner = None

        if not learner or not learner.public_share:
            return render(request,
                          template_name='public/public_badge.html',
                          dictionary={'no_public': True, 'state': state, 'user': user})

        achieved = False
        badge = None
        if badge_id and GamificationBadgeTemplate.objects.filter(id=badge_id).exists():
            badge = GamificationBadgeTemplate.objects.get(id=badge_id)
            if ParticipantBadgeTemplateRel.objects.filter(participant_id=participant_id,
                                                          badgetemplate_id=badge_id).exists():
                achieved = True
                badge.achieved = True
        else:
            return render(request,
                          template_name='public/public_badge.html',
                          dictionary={'no_public': True, 'state': state, 'user': user})

        fb = {}
        if achieved:
            if learner.first_name and learner.last_name:
                fb['description'] = '{0:s} {1:s} has earned the {2:s} badge on dig-it!'.format(learner.first_name,
                                                                                               learner.last_name,
                                                                                               badge.name)
            elif learner.first_name:
                fb['description'] = '{0:s} has earned the {1:s} badge on dig-it!'.format(learner.first_name,
                                                                                         badge.name)
            else:
                fb['description'] = 'Anon has earned the {0:s} badge on dig-it!'.format(badge.name)

        return render(request,
                      template_name='public/public_badge.html',
                      dictionary={'fb': fb,
                                  'badge': badge,
                                  'learner': learner,
                                  'participant': participant,
                                  'state': state,
                                  'user': user})

    return resolve_http_method(request, [get])


@oneplus_check_user
def level(request, state, user):
    def get():
        participant_id = request.GET.get('p', None)

        learner = None
        participant = None
        if participant_id and Participant.objects.filter(id=participant_id).exists():
            participant = Participant.objects.get(id=participant_id)
            learner = Learner.objects.get(participant__id=participant_id)
            if not learner.public_share:
                learner = None

        if not learner or not learner.public_share:
            return render(request,
                          template_name='public/public_level.html',
                          dictionary={'no_public': True, 'state': state, 'user': user})

        level, points_remaining = participant.calc_level()

        if learner.first_name and learner.last_name:
            learner_label = '{0:s} {1:s}'.format(learner.first_name, learner.last_name)
        elif learner.first_name:
            learner_label = learner.first_name
        else:
            learner_label = 'Anon'

        level, points_remaining = participant.calc_level()
        if level >= settings.MAX_LEVEL:
            level = settings.MAX_LEVEL
            points_remaining = 0

        fb = {'description': '{0:s} has achieved level {1:d} on dig-it!'.format(learner_label, level)}

        return render(request,
                      template_name='public/public_level.html',
                      dictionary={'fb': fb,
                                  'learner': learner,
                                  'learner_label': learner_label,
                                  'level': level,
                                  'levels': range(1, settings.MAX_LEVEL + 1),
                                  'level_max': settings.MAX_LEVEL,
                                  'participant': participant,
                                  'points_remaining': points_remaining,
                                  'state': state,
                                  'user': user})

    return resolve_http_method(request, [get])
