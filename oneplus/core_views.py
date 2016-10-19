from __future__ import division
from django.shortcuts import render
from django.shortcuts import render
from communication.models import Message
from core.models import Participant
from oneplus.views import oneplus_participant_required
from oneplus.auth_views import resolve_http_method

__author__ = 'herman'


@oneplus_participant_required
def menu(request, participant, state, user):
    _participant = participant
    request.session["state"]["inbox_unread"] = Message.unread_message_count(
        _participant.learner,
        _participant.classs.course
    )

    if "event_session" in request.session.keys():
        del request.session['event_session']

    def get():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    def post():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    return resolve_http_method(request, [get, post])
