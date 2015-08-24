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
    EventParticipantRel, EventSplashPage, EventStartPage, EventQuestionRel, EventQuestionAnswer, \
    EventEndPage, SUMitLevel, SUMit, SUMitEndPage
from core.models import Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel, Setting, \
    ParticipantRedoQuestionAnswer
from gamification.models import GamificationScenario
from organisation.models import CourseModuleRel
from oneplus.models import LearnerState
from oneplus.utils import update_metric
from oneplus.views import oneplus_state_required, oneplus_login_required, _content_profanity_check
from oneplus.auth_views import resolve_http_method
from oneplusmvp import settings
from django.db.models import Count, Sum
from oneplus.tasks import update_all_perc_correct_answers, update_num_question_metric
from requests.sessions import session


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

    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()
                                  ).first()

    if "event_session" in request.session.keys():
        del request.session['event_session']

    event_name = None
    first_sitting = True
    sumit = None
    if _event:
        allowed, _event_participant_rel = _participant.can_take_event(_event)
        if _event.type != 0:
            if allowed:
                event_name = _event.name
                if _event_participant_rel:
                    first_sitting = False
        else:
            sumit = {}
            event_name = _event.name
            _sumit_level = SUMitLevel.objects.filter(order=learnerstate.sumit_level).first()
            if _sumit_level:
                sumit["url"] = _sumit_level.image.url
                sumit["level"] = _sumit_level.name
            else:
                learnerstate.sumit_level = 1
                learnerstate.sumit_question = 1
                learnerstate.save()
                _sumit_level = SUMitLevel.objects.get(order=learnerstate.sumit_level)
                sumit["url"] = _sumit_level.image.url
                sumit["level"] = _sumit_level.name

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
        = ParticipantBadgeTemplateRel.objects \
        .filter(participant=_participant) \
        .count()
    request.session["state"]["home_position"] = Participant.objects.filter(
        classs=_participant.classs,
        points__gt=_participant.points
    ).count() + 1

    # Force week day to be Monday, when Saturday or Sunday
    request.session["state"]["home_day"] = learnerstate.get_week_day()

    if not sumit:
        request.session["state"]["home_tasks_today"] = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).count()
    else:
        request.session["state"]["home_tasks_today"] = EventQuestionAnswer.objects.filter(
            event=_event,
            participant=_participant,
            answer_date__gte=date.today()
        ).count()

    request.session["state"]["home_tasks_week"] \
        = learnerstate.get_questions_answered_week()

    request.session["state"]["home_required_tasks"] \
        = learnerstate.get_total_questions()

    if not sumit:
        request.session["state"]["home_tasks"] = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=_start_of_week
        ).count()
        request.session["state"]["home_correct"] = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            correct=True,
            answerdate__gte=_start_of_week
        ).count()
    else:
        request.session["state"]["home_tasks"] = EventQuestionAnswer.objects.filter(
            event=_event,
            participant=_participant,
            answer_date__gte=_start_of_week
        ).count()
        request.session["state"]["home_correct"] = EventQuestionAnswer.objects.filter(
            event=_event,
            participant=_participant,
            correct=True,
            answer_date__gte=_start_of_week
        ).count()
    request.session["state"]["home_goal"] = settings.ONEPLUS_WIN_REQUIRED - request.session["state"]["home_correct"]

    redo = None
    redo_active = Setting.get_setting("REPEATING_QUESTIONS_ACTIVE")

    if redo_active and redo_active == "true":
        if (request.session["state"]["home_tasks_week"] >= 15) or \
                (request.session["state"]["home_tasks_today"] >= request.session["state"]["home_required_tasks"]):
            correct = ParticipantQuestionAnswer.objects.filter(
                participant=_participant, correct=True).distinct().values('question')
            redo_correct = ParticipantRedoQuestionAnswer.objects.filter(
                participant=_participant, correct=True).distinct().values('question')
            answered = ParticipantQuestionAnswer.objects.filter(
                participant=_participant).distinct().values('question')
            questions = TestingQuestion.objects.filter(id__in=answered). \
                exclude(id__in=correct). \
                exclude(id__in=redo_correct)

            if questions:
                redo = True

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
                                                   "user": user,
                                                   "first_sitting": first_sitting,
                                                   "event_name": event_name,
                                                   "redo": redo,
                                                   "sumit": sumit})

    def post():
        if "take_event" in request.POST.keys():
            if not _event or not allowed:
                return get()
            else:
                if _event_participant_rel:
                    _event_participant_rel.sitting_number += 1
                    _event_participant_rel.save()
                    request.session["event_session"] = True
                    return redirect("learn.event")
                else:
                    return redirect("learn.event_start_page")
        return get()

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

    points = " - %d point question" % _learnerstate.active_question.points
    if Setting.objects.get(key="SHOW_POINT_ALLOCATION").value != "True" or _learnerstate.active_question.points is None:
        points = ""

    golden_egg = {}

    if (len(_learnerstate.get_answers_this_week()) + _learnerstate.get_num_questions_answered_today() + 1) == \
            _learnerstate.golden_egg_question:
        golden_egg["question"] = True
        golden_egg["url"] = Setting.objects.get(key="GOLDEN_EGG_IMG_URL").value

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
            "golden_egg": golden_egg,
            "points": points
        })

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

            try:
                update_all_perc_correct_answers.delay()
            except Exception as e:
                pass

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

                if _total_correct == 15:
                    _participant.award_scenario(
                        "15_CORRECT",
                        _learnerstate.active_question.module
                    )

                if _total_correct == 30:
                    _participant.award_scenario(
                        "30_CORRECT",
                        _learnerstate.active_question.module
                    )

                if _total_correct % 100 == 0:
                    _participant.award_scenario(
                        "100_CORRECT",
                        _learnerstate.active_question.module
                    )

                last_3 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:3]

                if last_3.count() == 3 \
                        and len([i for i in last_3 if i.correct]) == 3:
                    last_3 = ParticipantQuestionAnswer.objects.filter(
                        participant=_participant
                    ).order_by("answerdate").reverse()[3:6]
                    if last_3.count() == 0 or (last_3.count() == 3 and len([i for i in last_3 if i.correct]) == 3):
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
        else:
            return redirect("learn.home")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def redo(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant__id=user["participant_id"]
    ).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    # check if new question required then show question
    _learnerstate.get_next_redo_question()

    answered = ParticipantQuestionAnswer.objects.filter(
        participant=_learnerstate.participant
    ).distinct().values_list('question')
    correct = ParticipantQuestionAnswer.objects.filter(
        participant=_learnerstate.participant, correct=True
    ).distinct().values_list('question')
    questions = TestingQuestion.objects.filter(id__in=answered).exclude(id__in=correct)

    if not questions:
        return redirect("learn.home")

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        return render(request, "learn/redo.html", {
            "state": state,
            "user": user,
            "question": _learnerstate.redo_question,
        })

    def post():
        request.session["state"]["report_sent"] = False

        # answer provided
        if "answer" in request.POST.keys():
            _ans_id = request.POST["answer"]

            options = _learnerstate.redo_question.testingquestionoption_set
            try:
                _option = options.get(pk=_ans_id)
            except TestingQuestionOption.DoesNotExist:
                return redirect("learn.redo")

            _learnerstate.active_redo_result = _option.correct
            _learnerstate.save()

            # Answer question
            _participant.answer_redo(_option.question, _option)

            # Check for awards
            if _option.correct:
                return redirect("learn.redo_right")
            else:
                return redirect("learn.redo_wrong")
        else:
            return redirect("learn.home")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def redo_right(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    questions = len(_learnerstate.get_redo_questions())

    _usr = Learner.objects.get(pk=user["id"])
    request.session["state"]["banned"] = _usr.is_banned()

    def get():
        if _learnerstate.active_redo_result:
            # Max discussion page
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
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
                    question=_learnerstate.redo_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/redo_right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.redo_question,
                    "messages": _messages,
                    "questions": questions
                }
            )
        else:
            return HttpResponseRedirect("redo_wrong")

    def post():
        if _learnerstate.active_redo_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys() and request.POST["comment"] != "":
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
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
                    question=_learnerstate.redo_question,
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
                request.session["state"]["discussion_response_id"] \
                    = request.POST["comment_response_button"]

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/redo_right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.redo_question,
                    "messages": _messages,
                }
            )
        else:
            return HttpResponseRedirect("redo_wrong")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def redo_wrong(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"
    questions = len(_learnerstate.get_redo_questions())

    _usr = Learner.objects.get(pk=user["id"])

    request.session["state"]["banned"] = _usr.is_banned()

    def get():
        if not _learnerstate.active_redo_result:
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
                    moderated=True,
                    reply=None
                ).count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/redo_wrong.html",
                {"state": state,
                 "user": user,
                 "question": _learnerstate.redo_question,
                 "messages": _messages,
                 "questions": questions
                 }
            )
        else:
            return HttpResponseRedirect("redo_right")

    def post():
        if not _learnerstate.active_redo_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys() and request.POST["comment"] != "":
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
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
                    question=_learnerstate.redo_question,
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
                request.session["state"]["discussion_response_id"] \
                    = request.POST["comment_response_button"]

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.redo_question,
                    moderated=True,
                    reply=None
                ).order_by("-publishdate")[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/redo_wrong.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.redo_question,
                    "messages": _messages
                }
            )
        else:
            return HttpResponseRedirect("right")

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()
                                  ).first()
    if not _event or "event_session" not in request.session.keys():
        if "event_session" in request.session.keys():
            del request.session["event_session"]
        return redirect("learn.home")

    _event_question = _event.get_next_event_question(_participant)

    if not _event_question:
        return redirect("learn.home")

    _answered = EventQuestionAnswer.objects.filter(participant=_participant, event=_event) \
        .aggregate(Count('question'))['question__count']
    _total_questions = EventQuestionRel.objects.filter(event=_event).aggregate(Count('question'))['question__count']

    def get():
        return render(
            request,
            "learn/event.html",
            {
                "state": state,
                "user": user,
                "sittings": _event.number_sittings,
                "event_questions_answered": _answered,
                "total_event_questions": _total_questions,
                "question": _event_question,
            }
        )

    def post():
        if "answer" in request.POST.keys():
            _event_ans_id = request.POST["answer"]

            options = _event.get_next_event_question(_participant).testingquestionoption_set
            try:
                _option = options.get(pk=_event_ans_id)
            except TestingQuestionOption.DoesNotExist:
                return get()

            _participant.answer_event(_event, _option.question, _option)

            if _option.correct:
                return redirect("learn.event_right")

            return redirect("learn.event_wrong")

        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event_right(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if not _event or "event_session" not in request.session.keys():
        if "event_session" in request.session.keys():
            del request.session['event_session']
        return redirect("learn.home")

    _question = EventQuestionAnswer.objects.filter(event=_event, participant=_participant) \
        .order_by("-answer_date").first().question

    _answered = EventQuestionAnswer.objects.filter(participant=_participant, event=_event, ) \
        .aggregate(Count('question'))['question__count']
    _total_questions = EventQuestionRel.objects.filter(event=_event).aggregate(Count('question'))['question__count']

    def get():
        return render(
            request,
            "learn/event_right.html",
            {
                "state": state,
                "user": user,
                "event_questions_answered": _answered,
                "total_event_questions": _total_questions,
                "question": _question,
            }
        )

    def post():
        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event_wrong(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if not _event or "event_session" not in request.session.keys():
        if "event_session" in request.session.keys():
            del request.session['event_session']
        return redirect("learn.home")

    _question = EventQuestionAnswer.objects.filter(event=_event, participant=_participant) \
        .order_by("-answer_date").first().question

    _answered = EventQuestionAnswer.objects.filter(participant=_participant, event=_event, ) \
        .aggregate(Count('question'))['question__count']
    _total_questions = EventQuestionRel.objects.filter(event=_event).aggregate(Count('question'))['question__count']

    def get():
        return render(
            request,
            "learn/event_wrong.html",
            {
                "state": state,
                "user": user,
                "event_questions_answered": _answered,
                "total_event_questions": _total_questions,
                "question": _question,
            }
        )

    def post():
        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def sumit(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()
                                  ).first()

    if not _sumit:
        return redirect("learn.home")

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    request.session["state"]["next_tasks_today"] = \
        EventQuestionAnswer.objects.filter(
            event=_sumit,
            participant=_participant,
            answer_date__gte=date.today()
        ).distinct('participant', 'question').count() + 1

    _question = _sumit.get_next_sumit_question(_participant, _learnerstate.sumit_level, _learnerstate.sumit_question)

    sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level)
    sumit_question = _learnerstate.sumit_question

    sumit = {}
    sumit["name"] = sumit_level.name
    sumit["level"] = sumit_level.order
    for i in range(1, 4):
        if i in range(1, sumit_question):
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_04.png"
        else:
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_0%d.png" % i

    if not _question:
        return redirect("learn.home")

    def get():
        state["total_tasks_today"] = _learnerstate.get_total_questions()
        if state['next_tasks_today'] > state["total_tasks_today"]:
            return redirect("learn.home")

        return render(
            request,
            "learn/sumit.html",
            {
                "state": state,
                "user": user,
                "question": _question,
                "sumit": sumit
            }
        )

    def post():
        if "answer" in request.POST.keys():
            _event_ans_id = request.POST["answer"]

            options = _sumit.get_next_sumit_question(_participant, _learnerstate.sumit_level,
                                                     _learnerstate.sumit_question).testingquestionoption_set
            try:
                _option = options.get(pk=_event_ans_id)
            except TestingQuestionOption.DoesNotExist:
                return get()

            _participant.answer_event(_sumit, _option.question, _option)
            state["total_tasks_today"] = _learnerstate.get_total_questions()

            if _option.correct:
                _learnerstate.sumit_question += 1
                _learnerstate.save()
                if _learnerstate.sumit_question > 3:
                    _learnerstate.sumit_level += 1
                    _learnerstate.sumit_question = 1
                    _learnerstate.save()
                if _learnerstate.sumit_level > 5:
                    _learnerstate.sumit_level = 5
                    _learnerstate.save()
                return redirect("learn.sumit_right")
            else:
                _learnerstate.sumit_question = 1
                _learnerstate.save()
                return redirect("learn.sumit_wrong")

        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def sumit_right(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    _question = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant) \
        .order_by("-answer_date").first().question

    request.session["state"]["right_tasks_today"] = \
        EventQuestionAnswer.objects.filter(event=_sumit,
                                           participant=_participant, answer_date__gte=date.today()
                                           ).distinct('participant', 'question').count()

    sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level)
    sumit_question = _learnerstate.sumit_question

    sumit = dict()
    sumit["level"] = sumit_level.name
    for i in range(1, 4):
        if i in range(1, sumit_question):
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_04.png"
        else:
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_0%d.png" % i

    num_sumit_questions = SUMitLevel.objects.all().count() * _learnerstate.QUESTIONS_PER_DAY
    num_sumit_questions_answered = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).count()

    sumit["finished"] = None
    if num_sumit_questions == num_sumit_questions_answered:
        sumit["finished"] = True

    def get():
        return render(
            request,
            "learn/sumit_right.html",
            {
                "state": state,
                "user": user,
                "question": _question,
                "sumit": sumit
            }
        )

    def post():
        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def sumit_wrong(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    request.session["state"]["right_tasks_today"] = \
        EventQuestionAnswer.objects.filter(event=_sumit,
                                           participant=_participant, answer_date__gte=date.today()
                                           ).distinct('participant', 'question').count()

    sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level)
    sumit_question = _learnerstate.sumit_question

    _question = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant) \
        .order_by("-answer_date").first().question

    sumit = {}
    sumit["level"] = sumit_level.name
    for i in range(1, 4):
        if i in range(1, sumit_question):
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_04.png"
        else:
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_0%d.png" % i

    num_sumit_questions = SUMitLevel.objects.all().count() * _learnerstate.QUESTIONS_PER_DAY
    num_sumit_questions_answered = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).count()

    sumit["finsihed"] = None
    if num_sumit_questions == num_sumit_questions_answered:
        sumit["finished"] = True

    def get():
        return render(
            request,
            "learn/sumit_wrong.html",
            {
                "state": state,
                "user": user,
                "question": _question,
                "sumit": sumit
            }
        )

    def post():
        return get()

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


def get_event_points_awarded(participant):
    total_event_points = 0

    all_events = EventParticipantRel.objects.filter(participant=participant)
    for e in all_events:
        if e.event.event_points:
            total_event_questions = EventQuestionRel.objects.filter(event=e.event) \
                .aggregate(Count('question'))['question__count']
            participant_answers = EventQuestionAnswer.objects.filter(event=e.event, participant=participant)

            if total_event_questions == participant_answers:
                total_event_points += e.event.event_points

    return total_event_points


def get_badge_awarded(participant):
    # Get relevant badge related to scenario
    badgepoints = None
    badge = ParticipantBadgeTemplateRel.objects.filter(
        participant=participant,
        awarddate__range=[
            datetime.today() - timedelta(seconds=2),
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

    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    request.session["state"]["event_questions_answered"] = \
        EventQuestionAnswer.objects.filter(
            participant=_participant,
            event=_event,
        ).distinct('participant', 'question', 'event').count()
    request.session["state"]["total_event_questions"] = EventQuestionRel.objects.filter(event=_event).count()
    golden_egg = {}

    if _learnerstate.golden_egg_question == len(_learnerstate.get_answers_this_week()) + \
            _learnerstate.get_num_questions_answered_today():
        _golden_egg = get_golden_egg(_participant)
        if _golden_egg:
            if _golden_egg.point_value:
                golden_egg["message"] = "You've won this week's Golden Egg and %d points." % _golden_egg.point_value
                _participant.points += _golden_egg.point_value
                _participant.save()
            if _golden_egg.airtime:
                golden_egg["message"] = "You've won this week's Golden Egg and your share of R %d airtime. You will " \
                                        "be awarded your airtime next Monday." % _golden_egg.airtime
                mail_managers(subject="Golden Egg Airtime Award", message="%s %s %s won R %d airtime from a Golden Egg"
                                                                          % (_participant.learner.first_name,
                                                                             _participant.learner.last_name,
                                                                             _participant.learner.mobile,
                                                                             _golden_egg.airtime), fail_silently=False)
            if _golden_egg.badge:
                golden_egg["message"] = "You've won this week's Golden Egg and a badge"

                ParticipantBadgeTemplateRel(participant=_participant, badgetemplate=_golden_egg.badge.badge,
                                            scenario=_golden_egg.badge, awarddate=datetime.now()).save()
                if _golden_egg.badge.point and _golden_egg.badge.point.value:
                    _participant.points += _golden_egg.badge.point.value
                    _participant.save()

            golden_egg["url"] = Setting.objects.get(key="GOLDEN_EGG_IMG_URL").value
            GoldenEggRewardLog(participant=_participant, points=_golden_egg.point_value, airtime=_golden_egg.airtime,
                               badge=_golden_egg.badge).save()

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
            points = get_points_awarded(_participant) + get_event_points_awarded(_participant)

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
                    "golden_egg": golden_egg
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
                if request.session["state"]["discussion_page"] \
                        > request.session["state"]["discussion_page_max"]:
                    request.session["state"]["discussion_page"] \
                        = request.session["state"]["discussion_page_max"]
                request.session["state"]["discussion_response_id"] = None

            # show reply to comment comment
            elif "comment_response_button" in request.POST.keys():
                request.session["state"]["discussion_response_id"] \
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
                request.session["state"]["discussion_response_id"] \
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
def event_splash_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()
    if _event:
        if _event.type != 0:
            allowed, _event_participant_rel = _participant.can_take_event(_event)
            if not allowed:
                return redirect("learn.home")
    else:
        return redirect("learn.home")

    page = {}
    splash_pages = EventSplashPage.objects.filter(event=_event)
    num_splash_pages = len(splash_pages)
    random_splash_page = randint(1, num_splash_pages) - 1
    _splash_page = splash_pages[random_splash_page]
    page["header"] = _splash_page.header
    page["message"] = _splash_page.paragraph
    page["event_type"] = _event.type

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

    def post():
        return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event_start_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    sumit = None
    if _event:
        allowed, _event_participant_rel = _participant.can_take_event(_event)
        if _event.type != 0:
            if not allowed:
                return redirect("learn.home")
        else:
            sumit = True
            _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

            if _learnerstate is None:
                _learnerstate = LearnerState(participant=_participant)

            if _learnerstate.sumit_level <= 1:
                _learnerstate.sumit_level = 1
                _learnerstate.sumit_question = 1
                _learnerstate.save()

    else:
        return redirect("learn.home")

    page = {}
    start_page = EventStartPage.objects.filter(event=_event).first()
    page["header"] = start_page.header
    page["message"] = start_page.paragraph

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

    def post():
        if "event_start_button" in request.POST.keys():
            if _event_participant_rel:
                _event_participant_rel.sitting_number += 1
                _event_participant_rel.save()
            else:
                EventParticipantRel.objects.create(participant=_participant, event=_event, sitting_number=1)

            if not sumit:
                request.session["event_session"] = True

                return redirect("learn.event")
            else:
                _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

                if _learnerstate is None:
                    _learnerstate = LearnerState(participant=_participant)

                if _learnerstate.sumit_level <= 1:
                    _learnerstate.sumit_level = 1
                    _learnerstate.sumit_question = 1
                    _learnerstate.save()

                return redirect("learn.sumit")
        else:
            return get()

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def event_end_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _event = Event.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if "event_session" in request.session.keys():
        del request.session['event_session']

    page = {}

    _num_event_questions = EventQuestionRel.objects.filter(event=_event).count()
    _num_questions_answered = EventQuestionAnswer.objects.filter(event=_event, participant=_participant).count()

    if _num_event_questions == _num_questions_answered and not _num_questions_answered == 0 and \
            not _num_event_questions == 0:
        event_participant = EventParticipantRel.objects.filter(event=_event, participant=_participant).first()
        event_participant.results_received = True
        event_participant.save()

        _num_questions_correct = EventQuestionAnswer.objects.filter(event=_event, participant=_participant,
                                                                    correct=True).count()
        percentage = _num_questions_correct / _num_event_questions * 100

        end_page = EventEndPage.objects.filter(event=_event).first()
        page["header"] = end_page.header
        page["message"] = end_page.paragraph
        page["percentage"] = round(percentage)

        if _event.event_points:
            _participant.points += _event.event_points
            _participant.save()
        if _event.airtime:
            mail_managers(subject="Event Airtime Award", message="%s %s %s won R %d airtime from an event"
                                                                 % (_participant.learner.first_name,
                                                                    _participant.learner.last_name,
                                                                    _participant.learner.mobile,
                                                                    _event.airtime), fail_silently=False)
        if _event.event_badge:
            module = CourseModuleRel.objects.filter(course=_event.course).first()
            _participant.award_scenario(
                _event.event_badge.event,
                module
            )

        if _event.type == 1:
            module = CourseModuleRel.objects.filter(course=_event.course).first()
            _participant.award_scenario(
                "SPOT_TEST",
                module
            )
            _num_spot_tests = EventParticipantRel.objects.filter(event__type=1,
                                                                 participant=_participant).count()
            if _num_spot_tests > 0 and _num_spot_tests % 5 == 0:
                module = CourseModuleRel.objects.filter(course=_event.course).first()
                _participant.award_scenario(
                    "5_SPOT_TEST",
                    module
                )

        if _event.type == 2:
            module = CourseModuleRel.objects.filter(course=_event.course).first()
            _participant.award_scenario(
                "EXAM",
                module
            )
    else:
        return redirect("learn.home")
    badge, badge_points = get_badge_awarded(_participant)

    def get():
        return render(
            request,
            "learn/event_end_page.html",
            {
                "state": state,
                "user": user,
                "page": page,
                "badge": badge,
            }
        )

    return resolve_http_method(request, [get])


@oneplus_state_required
@oneplus_login_required
def sumit_end_page(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    page = {}
    sumit = {}
    sumit["points"] = 0

    num_sumit_questions = SUMitLevel.objects.all().count() * _learnerstate.QUESTIONS_PER_DAY
    num_sumit_questions_answered = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).count()

    if num_sumit_questions == num_sumit_questions_answered:
        if _learnerstate.sumit_level in range(1, 5):
            end_page = SUMitEndPage.objects.get(event=_sumit, type=1)
        elif _learnerstate.sumit_level == 5:
            num_sumit_questions_correct = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant,
                                                                             correct=True).count()
            if num_sumit_questions_correct == num_sumit_questions:
                end_page = SUMitEndPage.objects.get(event=_sumit, type=3)

                if _sumit.event_point:
                    sumit["points"] = _sumit.event_points
                    _participant.points += _sumit.event_points
                    _participant.save()
            else:
                end_page = SUMitEndPage.objects.get(event=_sumit, type=2)

        sumit["level"] = SUMitLevel.objects.get(order=_learnerstate.sumit_level).name
        points = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant, correct=True)\
            .aggregate(Sum='question__points')['question__points__sum']
        sumit["points"] += points

        page["header"] = end_page.header
        page["message"] = end_page.paragraph

        if _sumit.airtime:
            mail_managers(subject="SUMit! Airtime Award", message="%s %s %s won R %d airtime from an event"
                                                                  % (_participant.learner.first_name,
                                                                     _participant.learner.last_name,
                                                                     _participant.learner.mobile,
                                                                     _sumit.airtime), fail_silently=False)
        if _sumit.event_badge:
            module = CourseModuleRel.objects.filter(course=_sumit.course).first()
            _participant.award_scenario(
                _sumit.event_badge.event,
                module
            )

        _learnerstate.sumit_level = 0
        _learnerstate.sumit_question = 0
        _learnerstate.save()
    else:
        return redirect("learn.home")
    badge, badge_points = get_badge_awarded(_participant)

    def get():
        return render(
            request,
            "learn/sumit_end_page.html",
            {
                "state": state,
                "user": user,
                "page": page,
                "badge": badge,
                "sumit": sumit
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
        if "issue" in request.POST.keys() and request.POST["issue"] != "" \
                and "fix" in request.POST.keys() and request.POST["fix"] != "":
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
