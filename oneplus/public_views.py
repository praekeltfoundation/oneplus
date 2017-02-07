from __future__ import division
import logging

from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from datetime import datetime
from auth.models import CustomUser, Learner
from core.models import Participant, TestingQuestion
from oneplus.auth_views import resolve_http_method
from oneplus.views import oneplus_check_user

logger = logging.getLogger(__name__)


@oneplus_check_user
def badges(request, state, user):
    def get():
        pass

    return resolve_http_method(request, [get])
