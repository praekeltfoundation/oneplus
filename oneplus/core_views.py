from __future__ import division
from django.shortcuts import render
from django.shortcuts import render
from communication.models import Message
from core.models import Participant
from oneplus.views import oneplus_state_required, oneplus_login_required
from oneplus.auth_views import resolve_http_method

__author__ = 'herman'


@oneplus_state_required
@oneplus_login_required
def menu(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    request.session["state"]["inbox_unread"] = Message.unread_message_count(
        _participant.learner,
        _participant.classs.course
    )
    if "in_event" in state:
        if state["in_event"]:
            state["in_event"] = False

    def get():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    def post():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    return resolve_http_method(request, [get, post])
