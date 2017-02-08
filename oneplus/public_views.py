from __future__ import division
import logging

from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from datetime import datetime
from auth.models import CustomUser, Learner
from core.models import Participant, TestingQuestion
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
                          dictionary={'no_public': True})

        badge = None
        if badge_id and GamificationBadgeTemplate.objects.filter(id=badge_id).exists():
            badge = GamificationBadgeTemplate.objects.get(id=badge_id)
        else:
            return render(request,
                          template_name='public/public_badge.html',
                          dictionary={'no_public': True})

        return render(request,
                      template_name='public/public_badge.html',
                      dictionary={'badge': badge, 'learner': learner, 'participant': participant})

    return resolve_http_method(request, [get])
