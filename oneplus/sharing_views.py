from __future__ import division
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from oneplus.views import oneplus_participant_required
from oneplus.auth_views import resolve_http_method
from oneplus.leaderboard_utils import get_school_leaderboard, get_national_leaderboard, get_class_leaderboard


@oneplus_participant_required
def level(request, state, user, participant):
    if not settings.SOCIAL_MEDIA_ACTIVE:
        return redirect('arrive')

    # get learner state
    _participant = participant
    learner = _participant.learner

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

    allow_sharing = participant.learner.public_share

    def get():
        if not participant.learner.public_share:
            return redirect('learn.home')

        share_url = '{0:s}?p={1:d}'.format(reverse('public:level'), participant.id)
        return render(request, "sharing/level_sharing.html", {
            "allow_sharing": allow_sharing,
            "learner_label": learner_label,
            "level": level,
            "level_max": settings.MAX_LEVEL,
            "levels": range(1, settings.MAX_LEVEL + 1),
            "participant": _participant,
            "points_remaining": points_remaining,
            "share_url": share_url,
            "state": state,
            "user": user})

    return resolve_http_method(request, [get])


@oneplus_participant_required
def leaderboard(request, state, user, participant, board_type=''):
    if not settings.SOCIAL_MEDIA_ACTIVE:
        return redirect('arrive')

    max_uncollapsed = 3

    if board_type == 'class':
        share_board = get_class_leaderboard(participant, max_uncollapsed)
    elif board_type == 'school':
        share_board = get_school_leaderboard(participant, max_uncollapsed)
    elif board_type == 'national':
        share_board = get_national_leaderboard(participant, max_uncollapsed)

    share_url = '{0:s}?p={1:d}'.format(reverse('public:leaderboard', kwargs={'board_type': board_type}), participant.id)

    def get():
        if not participant.learner.public_share:
            return redirect('learn.home')

        return render(request, 'sharing/leaderboards_sharing.html', {
            "allow_sharing": participant.learner.public_share,
            "share_board": share_board,
            "participant": participant,
            "share_url": share_url,
            "state": state,
            "user": user})

    return resolve_http_method(request, [get])
