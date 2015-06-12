from __future__ import division

from datetime import date, timedelta, datetime
from random import randint

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.core.mail import mail_managers
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from auth.models import Learner
from communication.models import Discussion, Report
from content.models import TestingQuestion, TestingQuestionOption, GoldenEgg, GoldenEggRewardLog, Event, \
    EventParticipantRel, EventPageRel, EventSplashPage, EventStartPage, EventQuestionRel, EventQuestionAnswer, \
    EventEndPage
from core.models import Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel
from gamification.models import GamificationScenario
from oneplus.models import LearnerState
from oneplus.utils import update_metric
from oneplus.views import oneplus_state_required, oneplus_login_required, _content_profanity_check
from oneplus.auth_views import resolve_http_method
from oneplusmvp import settings


@oneplus_state_required
@oneplus_login_required
def home(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _start_of_week = date.today() - timedelta(date.today().weekday())
    learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    if learnerstate is None:
        learnerstate = LearnerState(participant=_participant)

    answered = ParticipantQuestionAnswer.objects.filter(
        participant=learnerstate.participant
    ).distinct().values_list('question')

    questions = TestingQuestion.objects.filter(
        module__in=learnerstate.participant.classs.course.modules.all(),
        module__is_active=True,
        state=3
    ).exclude(id__in=answered)

    learner = learnerstate.participant.learner

    if not questions:
        request.session["state"]["questions_complete"] = True
        subject = ' '.join([
            'Questions Completed -',
            learner.first_name,
            learner.last_name,
            '-',
            learner.username
        ])
        message = '\n'.join([
            'Questions completed',
            'Student: ' + learner.first_name + ' ' + learner.last_name,
            'Msisdn: ' + learner.username
        ])

        mail_managers(
            subject=subject,
            message=message,
            fail_silently=False
        )

    else:
        request.session["state"]["questions_complete"] = False

    request.session["state"]["home_points"] = _participant.points
    request.session["state"]["home_badges"] \
        = ParticipantBadgeTemplateRel.objects\
        .filter(participant=_participant)\
        .count()
    request.session["state"]["home_position"]\
        = Participant.objects.filter(
            classs=_participant.classs,
            points__gt=_participant.points
        ).count() + 1

    # Force week day to be Monday, when Saturday or Sunday
    request.session["state"]["home_day"] = learnerstate.get_week_day()

    request.session["state"]["home_tasks_today"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).count()

    request.session["state"]["home_tasks_week"]\
        = learnerstate.get_questions_answered_week()

    request.session["state"]["home_required_tasks"]\
        = learnerstate.get_total_questions()

    request.session["state"]["home_tasks"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=_start_of_week
        ).count()
    request.session["state"]["home_correct"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            correct=True,
            answerdate__gte=_start_of_week
        ).count()
    request.session["state"]["home_goal"]\
        = settings.ONEPLUS_WIN_REQUIRED\
        - request.session["state"]["home_correct"]

    def get():
        _learner = Learner.objects.get(id=user['id'])
        if _learner.last_active_date is None:
            _learner.last_active_date = datetime.now() - timedelta(days=33)

        last_active = _learner.last_active_date.date()
        now = datetime.now().date()
        days_ago = now - last_active

        if days_ago >= timedelta(days=1):
            _learner.last_active_date = datetime.now()
            _learner.save()
            update_metric("running.active.participants24", 1, "SUM")
        if days_ago >= timedelta(days=32):
            update_metric("running.active.participantsmonth", 1, "SUM")
        if days_ago >= timedelta(days=7):
            update_metric("running.active.participants7", 1, "SUM")
        if days_ago >= timedelta(days=2):
                update_metric("running.active.participants48", 1, "SUM")

        return render(request, "learn/home.html", {"state": state,
                                                   "user": user})

    def post():
        return render(request, "learn/home.html", {"state": state,
                                                   "user": user})

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def nextchallenge(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant__id=user["participant_id"]
    ).first()
    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    # check if new question required then show question
    _learnerstate.getnextquestion()

    answered = ParticipantQuestionAnswer.objects.filter(
        participant=_learnerstate.participant
    ).distinct().values_list('question')
    questions = TestingQuestion.objects.filter(
        module__in=_learnerstate.participant.classs.course.modules.filter(type=1),
        module__is_active=True,
        state=3
    ).exclude(id__in=answered)

    if not questions:
        return redirect("learn.home")

    request.session["state"]["next_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count() + 1

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        state["total_tasks_today"] = _learnerstate.get_total_questions()
        if state['next_tasks_today'] > state["total_tasks_today"]:
            return redirect("learn.home")

        return render(request, "learn/next.html", {
            "state": state,
            "user": user,
            "question": _learnerstate.active_question,
        })

    def update_num_question_metric():
        update_metric(
            "total.questions",
            1,
            metric_type="SUM"
        )

    def update_perc_correct_answers(name, days_ago):
        date_range = (
            datetime.now().date() - timedelta(days=days_ago),
            datetime.now(),
        )
        total = ParticipantQuestionAnswer.objects.filter(
            answerdate__range=date_range
        ).count()
        if total > 0:
            value = ParticipantQuestionAnswer.objects.filter(
                answerdate__range=date_range,
                correct=True
            ).count() / total
        else:
            value = 0
        update_metric(
            "questions.correct." + name,
            value * 100,
            "LAST"
        )

    def update_all_perc_correct_answers():
        # Update metrics
        update_perc_correct_answers('24hr', 1)
        update_perc_correct_answers('48hr', 2)
        update_perc_correct_answers('7days', 7)
        update_perc_correct_answers('32days', 32)

    def post():
        request.session["state"]["report_sent"] = False

        # answer provided
        if "answer" in request.POST.keys():
            _ans_id = request.POST["answer"]

            options = _learnerstate.active_question.testingquestionoption_set
            try:
                _option = options.get(pk=_ans_id)
            except TestingQuestionOption.DoesNotExist:
                return redirect("learn.next")

            _learnerstate.active_result = _option.correct
            _learnerstate.save()

            # Answer question
            _participant.answer(_option.question, _option)

            # Update metrics
            update_num_question_metric()
            update_all_perc_correct_answers()

            # Check for awards
            if _option.correct:

                # Important
                _total_correct = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant,
                    correct=True
                ).count()

                if _total_correct == 1:
                    _participant.award_scenario(
                        "1_CORRECT",
                        _learnerstate.active_question.module
                    )

                if _total_correct >= 15:
                    _participant.award_scenario(
                        "15_CORRECT",
                        _learnerstate.active_question.module
                    )

                if _total_correct >= 30:
                    _participant.award_scenario(
                        "30_CORRECT",
                        _learnerstate.active_question.module
                    )

                if _total_correct >= 100:
                    _participant.award_scenario(
                        "100_CORRECT",
                        _learnerstate.active_question.module
                    )

                last_3 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:3]

                if last_3.count() == 3 \
                        and len([i for i in last_3 if i.correct]) == 3:
                    _participant.award_scenario(
                        "3_CORRECT_RUNNING",
                        _learnerstate.active_question.module
                    )

                last_5 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:5]

                if last_5.count() == 5 \
                        and len([i for i in last_5 if i.correct]) == 5:
                    _participant.award_scenario(
                        "5_CORRECT_RUNNING",
                        _learnerstate.active_question.module
                    )

                return redirect("learn.right")

            else:
                return redirect("learn.wrong")

        state["total_tasks_today"] = _learnerstate.get_total_questions()

        return render(
            request,
            "learn/next.html",
            {
                "state": state,
                "user": user,
                "question": _learnerstate.active_question,
            }
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def adminpreview(request, questionid):
    question = TestingQuestion.objects.get(id=questionid)

    def get():
        messages = Discussion.objects.filter(
            question=question,
            moderated=True,
            reply=None
        ).order_by("-publishdate")

        return render(request, "learn/next.html", {
            "question": question,
            "messages": messages,
            "preview": True
        })

    def post():
        # answer provided
        if "answer" in request.POST.keys():
            ans_id = request.POST["answer"]
            option = question.testingquestionoption_set.get(pk=ans_id)

            if option.correct:
                return HttpResponseRedirect("right/%s" % questionid)

            else:
                return HttpResponseRedirect("wrong/%s" % questionid)

        messages = Discussion.objects.filter(
            question=question,
            moderated=True,
            reply=None
        ).order_by("-publishdate")

        return render(request, "learn/next.html", {
            "question": question,
            "messages": messages,
            "preview": True
        })

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def adminpreview_right(request, questionid):
    def get():
        question = TestingQuestion.objects.get(id=questionid)

        # Messages for discussion page
        messages = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                reply=None
            ).order_by("-publishdate")

        return render(
            request,
            "learn/right.html",
            {
                "question": question,
                "messages": messages,
                "points": 1,
                "preview": True
            }
        )

    return resolve_http_method(request, [get])


@user_passes_test(lambda u: u.is_staff)
def adminpreview_wrong(request, questionid):
    def get():
        question = TestingQuestion.objects.get(id=questionid)

        # Messages for discussion page
        messages = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                reply=None
            ).order_by("-publishdate")

        return render(
            request,
            "learn/wrong.html",
            {
                "question": question,
                "messages": messages,
                "preview": True
            }
        )

    return resolve_http_method(request, [get])


def get_points_awarded(participant):
    # Get current participant question answer
    answer = ParticipantQuestionAnswer.objects.filter(
        participant=participant,
    ).latest('answerdate')

    # Get question
    question = answer.question

    # Get points
    if question.points is 0:
        question.points = 1
        question.save()

    return question.points


def get_badge_awarded(participant):
    # Get relevant badge related to scenario
    badgepoints = None
    badge = ParticipantBadgeTemplateRel.objects.filter(
        participant=participant,
        awarddate__range=[
            datetime.today()-timedelta(seconds=2),
            datetime.today()
        ]
    ).order_by('-awarddate').first()

    if badge:
        badgetemplate = badge.badgetemplate
        badgepoints = GamificationScenario.objects.get(
            badge__id=badgetemplate.id
        ).point
    else:
        badgetemplate = None

    return badgetemplate, badgepoints,


def ts_awarded(participant):
    # Get current participant question answer
    answer = ParticipantQuestionAnswer.objects.filter(
        participant=participant,
    ).latest('answerdate')

    # Get question
    question = answer.question

    # Get points
    if question.points is 0:
        question.points = 1
        question.save()

    return question.points


def get_golden_egg(participant):
    golden_egg = GoldenEgg.objects.filter(
        classs=participant.classs,
        active=True
    ).first()
    if not golden_egg:
        golden_egg = GoldenEgg.objects.filter(
            course=participant.classs.course,
            classs=None,
            active=True
        ).first()
    return golden_egg


@oneplus_state_required
@oneplus_login_required
def right(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    request.session["state"]["right_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count()
    golden_egg = {}
    if _learnerstate.golden_egg_question == len(_learnerstate.get_answers_this_week()) + \
            _learnerstate.get_num_questions_answered_today():
        _golden_egg = get_golden_egg(_participant)
        if _golden_egg.point_value:
            golden_egg["message"] = "You've won this week's Golden Egg and %d points." % _golden_egg.point_value
            _participant.points += _golden_egg.point_value
            _participant.save()
        if _golden_egg.airtime:
            golden_egg["message"] = "You've won this week's Golden Egg and your share of R %d airtime. You will be " \
                                    "awarded your airtime next Monday." % _golden_egg.airtime
            mail_managers(subject="Golden Egg Airtime Award", message="%s %s %s won R %d airtime from a Golden Egg"
                                                                      % (_participant.learner.first_name,
                                                                         _participant.learner.last_name,
                                                                         _participant.learner.mobile,
                                                                         _golden_egg.airtime), fail_silently=False)
        if _golden_egg.badge:
            golden_egg["message"] = "You've won this week's Golden Egg and a badge"
            ParticipantBadgeTemplateRel(participant=_participant, badgetemplate=_golden_egg.badge.badge,
                                        scenario=_golden_egg.badge, awarddate=datetime.now()).save()
            _participant.points += _golden_egg.badge.point.value
            _participant.save()
        golden_egg["url"] = settings.GOLDEN_EGG_IMG_URL
        GoldenEggRewardLog(participant=_participant, points=_golden_egg.point_value, airtime=_golden_egg.airtime,
                           badge=_golden_egg.badge).save()

    print GoldenEggRewardLog.objects.filter(participant=_participant)

    state["total_tasks_today"] = _learnerstate.get_total_questions()

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    _usr = Learner.objects.get(pk=user["id"])
    request.session["state"]["banned"] = _usr.is_banned()

    def get():
        if _learnerstate.active_result:
            # Max discussion page
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).count()

            # Discussion page?
            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            # Messages for discussion page
            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            # Get badge points
            badge, badge_points = get_badge_awarded(_participant)
            points = get_points_awarded(_participant)

            return render(
                request,
                "learn/right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question,
                    "messages": _messages,
                    "badge": badge,
                    "points": points,
                    "golden_egg": golden_egg,
                }
            )
        else:
            return HttpResponseRedirect("wrong")

    def post():
        if _learnerstate.active_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys() and request.POST["comment"] != "":
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    reply=None,
                    content=_comment,
                    author=_usr,
                    publishdate=datetime.now(),
                    moderated=True
                )
                _message.save()
                _content_profanity_check(_message)
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None

            elif "reply" in request.POST.keys() and request.POST["reply"] != "":
                _comment = request.POST["reply"]
                _parent = Discussion.objects.get(
                    pk=request.POST["reply_button"]
                )
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    reply=_parent,
                    content=_comment,
                    author=_usr,
                    publishdate=datetime.now(),
                    moderated=True
                )
                _message.save()
                _content_profanity_check(_message)
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None

            # show more comments
            elif "page" in request.POST.keys():
                request.session["state"]["discussion_page"] += 2
                if request.session["state"]["discussion_page"]\
                        > request.session["state"]["discussion_page_max"]:
                    request.session["state"]["discussion_page"]\
                        = request.session["state"]["discussion_page_max"]
                request.session["state"]["discussion_response_id"] = None

            # show reply to comment comment
            elif "comment_response_button" in request.POST.keys():
                request.session["state"]["discussion_response_id"]\
                    = request.POST["comment_response_button"]

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question,
                    "messages": _messages,
                }
            )
        else:
            return HttpResponseRedirect("wrong")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def wrong(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    request.session["state"]["wrong_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count()
    state["total_tasks_today"] = _learnerstate.get_total_questions()

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    _usr = Learner.objects.get(pk=user["id"])

    request.session["state"]["banned"] = _usr.is_banned()

    def get():
        if not _learnerstate.active_result:
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/wrong.html",
                {"state": state,
                 "user": user,
                 "question": _learnerstate.active_question,
                 "messages": _messages
                 }
            )
        else:
            return HttpResponseRedirect("right")

    def post():
        if not _learnerstate.active_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys() and request.POST["comment"] != "":
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    reply=None,
                    content=_comment,
                    author=_usr,
                    publishdate=datetime.now(),
                    moderated=True
                )
                _message.save()
                _content_profanity_check(_message)
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None

            elif "reply" in request.POST.keys() and request.POST["reply"] != "":
                _comment = request.POST["reply"]
                _parent = Discussion.objects.get(
                    pk=request.POST["reply_button"]
                )
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    reply=_parent,
                    content=_comment,
                    author=_usr,
                    publishdate=datetime.now(),
                    moderated=True
                )
                _message.save()
                _content_profanity_check(_message)
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None

            # show more comments
            elif "page" in request.POST.keys():
                request.session["state"]["discussion_page"] += 2
                if request.session["state"]["discussion_page"] \
                        > request.session["state"]["discussion_page_max"]:
                    request.session["state"]["discussion_page"] \
                        = request.session["state"]["discussion_page_max"]
                request.session["state"]["discussion_response_id"] = None

            # show reply to comment comment
            elif "comment_response_button" in request.POST.keys():
                request.session["state"]["discussion_response_id"]\
                    = request.POST["comment_response_button"]

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/wrong.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question,
                    "messages": _messages
                }
            )
        else:
            return HttpResponseRedirect("right")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def discuss(request, state, user):
    def get():
        return render(request, "auth/discuss.html", {"state": state})

    def post():
        return render(request, "auth/discuss.html", {"state": state})

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event_splash_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__gte=datetime.now(),
                                  deactivation_date__lt=datetime.now()
                                  ).first()
    _event_participant_rel = EventParticipantRel.objects.filter(participant=_participant, event=_event)

    page = {}
    splash_pages = []

    if not _event_participant_rel and _event:
        pages = EventPageRel.objects.select_related('StartPage', 'EndPage', 'SplashPage').filter(event=_event)
        for page in pages:
            try:
                splash_pages.append(page.page.eventsplashpage)
            except EventSplashPage.DoesNotExist:
                continue
        num_splash_pages = len(splash_pages)
        random_splash_page = randint(1, num_splash_pages)
        _splash_page = splash_pages[random_splash_page]
        page["header"] = _splash_page.header
        page["message"] = _splash_page.message

    def get():
        return render(
            request,
            "learn/event_splash_page.html",
            {
                "state": state,
                "user": user,
                "page": page
            }
        )

    return resolve_http_method(request, [get])


@oneplus_state_required
@oneplus_login_required
def event_start_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__gte=datetime.now(),
                                  deactivation_date__lt=datetime.now()
                                  ).first()
    _event_participant_rel = EventParticipantRel.objects.filter(participant=_participant, event=_event)

    page = {}

    if not _event_participant_rel and _event:
        start_page = None
        pages = EventPageRel.objects.select_related('StartPage', 'EndPage', 'SplashPage').filter(event=_event)
        for page in pages:
            try:
                start_page = page.page.eventstartpage
                break
            except EventStartPage.DoesNotExist:
                continue
        page["header"] = start_page.header
        page["message"] = start_page.message

    def get():
        return render(
            request,
            "learn/event_start_page.html",
            {
                "state": state,
                "user": user,
                "page": page
            }
        )

    return resolve_http_method(request, [get])


@oneplus_state_required
@oneplus_login_required
def event_end_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__gte=datetime.now(),
                                  deactivation_date__lt=datetime.now()
                                  ).first()

    page = {}

    _num_event_questions = EventQuestionRel.objects.filter(event=_event).count()
    _num_questions_answered = EventQuestionAnswer.objects.filter(event=_event, participant=_participant).count()

    if _num_event_questions == _num_questions_answered:
        _num_questions_correct = EventQuestionAnswer.objects.filter(event=_event, participant=_participant,
                                                                    correct=True).count()
        percentage = _num_questions_correct / _num_event_questions * 100

        end_page = None
        pages = EventPageRel.objects.select_related('StartPage', 'EndPage', 'SplashPage').filter(event=_event)
        for page in pages:
            try:
                end_page = page.page.eventstartpage
                break
            except EventEndPage.DoesNotExist:
                continue

        page["header"] = end_page.header
        page["message"] = end_page.message
        page["percentage"] = percentage

    def get():
        return render(
            request,
            "learn/event_end_page.html",
            {
                "state": state,
                "user": user,
                "page": page
            }
        )

    return resolve_http_method(request, [get])


@oneplus_state_required
@oneplus_login_required
def report_question(request, state, user, questionid, frm):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()

    try:
        _question = TestingQuestion.objects.get(id=questionid)
    except ObjectDoesNotExist:
        return redirect("learn.home")

    if frm not in ['next', 'right', 'wrong']:
        return redirect("learn.home")

    def get():
        return render(
            request, "learn/report_question.html",
            {
                "state": state,
                "user": user,
                "question_number": _question.order,
            }
        )

    def post():
        if "issue" in request.POST.keys() and request.POST["issue"] != "" and \
                "fix" in request.POST.keys() and request.POST["fix"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _issue = request.POST["issue"]
            _fix = request.POST["fix"]

            _report = Report(
                user=_usr,
                question=_question,
                issue=_issue,
                fix=_fix,
                response=None
            )

            _report.save()

            state["report_sent"] = True

            # if _learnerstate.active_result:
            #     # Max discussion page
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).count()

            # Discussion page?
            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            # Messages for discussion page
            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return HttpResponseRedirect('/' + frm,
                                        {
                                            "state": state,
                                            "user": user,
                                            "question": _question,
                                            "messages": _messages,
                                        })
        else:
            return render(
                request, "learn/report_question.html",
                {
                    "state": state,
                    "user": user,
                    "question_number": _question.order,
                }
            )

    return resolve_http_method(request, [get, post])
