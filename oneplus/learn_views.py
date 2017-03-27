# -*- coding: utf-8 -*-
from __future__ import division
from datetime import date, timedelta, datetime
from random import randint

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.core.mail import mail_managers
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template import RequestContext
from auth.models import Learner
from communication.models import CoursePostRel, Discussion, DiscussionLike, Post, Report
from content.models import TestingQuestion, TestingQuestionOption, GoldenEgg, GoldenEggRewardLog, Event, \
    EventParticipantRel, EventSplashPage, EventStartPage, EventQuestionRel, EventQuestionAnswer, \
    EventEndPage, SUMitLevel, SUMit
from core.models import BadgeAwardLog, Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel, Setting
from gamification.models import GamificationScenario, GamificationBadgeTemplate
from organisation.models import CourseModuleRel
from oneplus.models import LearnerState
from oneplus.utils import update_metric
from oneplus.views import oneplus_participant_required, _content_profanity_check
from oneplus.auth_views import resolve_http_method
from oneplusmvp import settings
from django.db.models import Count, Sum
from oneplus.tasks import update_all_perc_correct_answers, update_num_question_metric
from django.utils import timezone
from django.contrib import messages
from communication.utils import report_user_post


def get_class_leaderboard_position(participant):
    leaderboard = Participant.objects.filter(classs=participant.classs, is_active=True) \
        .order_by("-points", 'learner__first_name')

    position_counter = 0
    for a in leaderboard:
        position_counter += 1
        if a.id == participant.id:
            return position_counter

    return None

array_of_statements = {
    "0": "You’ve completed your daily questions, you got {0:d}/{1:d} correct. Better luck next time.",
    "33": "You’ve completed your daily questions, you got {0:d}/{1:d} correct and earn a total of {2:d} points. "
          "Better luck next time",
    "34": "Well done! You’ve completed your daily questions. You got {0:d}/{1:d} correct and earned a "
          "total of {2:d} points.",
    "100": "Congrats! You’ve answered all questions for the day correctly and earned a total of {2:d} points. "
           "At this rate, you’ll be levelling up in no time."
}


@oneplus_participant_required
def home(request, state, user, participant):
    _participant = participant

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
            if not EventQuestionAnswer.objects.filter(event=_event, participant=_participant).exists() or \
                    learnerstate.sumit_level not in range(1, 6) or \
                    learnerstate.sumit_question not in range(1, 4):
                learnerstate.sumit_level = 1
                learnerstate.sumit_question = 1
                learnerstate.save()

            sumit = {}
            event_name = _event.name
            _sumit_level = SUMitLevel.objects.filter(order=learnerstate.sumit_level).first()
            sumit["url"] = _sumit_level.image.url
            sumit["level"] = _sumit_level.name

            #next level of current level
            sumit["next_level"] = SUMitLevel.objects.filter(order=learnerstate.sumit_level)

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
    request.session["state"]["home_goal"] = settings.ONEPLUS_WIN_REQUIRED
    request.session["state"]["home_goal_remaining"] = \
        settings.ONEPLUS_WIN_REQUIRED - request.session["state"]["home_correct"]

    redo = None
    redo_active = Setting.get_setting("REPEATING_QUESTIONS_ACTIVE")

    if redo_active and redo_active == "true":
        if (request.session["state"]["home_tasks_week"] >= 15) or \
                (request.session["state"]["home_tasks_today"] >= request.session["state"]["home_required_tasks"]):
            questions = learnerstate.get_redo_questions()

            if questions:
                redo = True

    level, points_remaining = participant.calc_level()
    if level >= settings.MAX_LEVEL:
        level = settings.MAX_LEVEL
        points_remaining = 0

    dt = timezone.now()
    _course = participant.classs.course
    post_list = CoursePostRel.objects.filter(course=_course, post__publishdate__lt=dt).\
        values_list('post__id', flat=True)
    try:
        _post = Post.objects.filter(
            id__in=post_list
        ).latest(field_name='publishdate')
    except:
        _post = None

    def get():
        _learner = Learner.objects.get(id=user['id'])
        if _learner.last_active_date is None:
            _learner.last_active_date = datetime.now() - timedelta(days=33)

        last_active = _learner.last_active_date.date()
        now = datetime.now().date()
        days_ago = now - last_active

        # Calculating which message to display on the home screen based on participant's marks
        num_correct, num_available = learnerstate.get_correct_of_available()
        num_answered = learnerstate.get_questions_answered_week()
        feedback_string = " "
        points_week = learnerstate.get_points_week()

        if num_answered == num_available:
            _range = (num_correct/num_available)*100

            if _range <= 0:
                feedback_string = array_of_statements["0"]
            elif _range < 34:
                feedback_string = array_of_statements["33"]
            elif _range < 100:
                feedback_string = array_of_statements["34"]
            elif _range >= 100:
                feedback_string = array_of_statements["100"]

            feedback_string = feedback_string.format(num_correct, num_available, points_week)

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

        sumit_answered_today = learnerstate.get_num_questions_answered_today()
        sumit_next_level = SUMitLevel.objects.get(order=learnerstate.sumit_level + 1).name
        sumit_day = learnerstate.get_day_of_sumit()
        sumit_correct_answers, temp = learnerstate.get_correct_of_available()
        sumit_day_flag = False

        temp = 3*sumit_day

        if temp != sumit_correct_answers:
            sumit_day_flag = False
        else:
            sumit_day_flag = True

        tempSCA = sumit_correct_answers % 3

        if sumit_correct_answers % 3 == 0:
            sumit_correct_answers = 0
        else:
            sumit_correct_answers /= 3

            if sumit_correct_answers > 0 or sumit_correct_answers < 0:
                tempSCA = 1
            elif sumit_correct_answers > 1 or sumit_correct_answers < 1:
                tempSCA = 2
            elif sumit_correct_answers > 2 or sumit_correct_answers < 2:
                tempSCA = 3
            elif sumit_correct_answers > 3 or sumit_correct_answers < 3:
                tempSCA = 4
            elif sumit_correct_answers > 4 or sumit_correct_answers < 4:
                tempSCA = 5

        return render(request, "learn/home.html", {"event_name": event_name,
                                                   "first_sitting": first_sitting,
                                                   "level": level,
                                                   "level_max": settings.MAX_LEVEL,
                                                   "levels": range(1, settings.MAX_LEVEL + 1),
                                                   "points_remaining": points_remaining,
                                                   "position": get_class_leaderboard_position(_participant),
                                                   "post": _post,
                                                   "public_sharing": _learner.public_share,
                                                   "redo": redo,
                                                   "state": state,
                                                   "learner": learnerstate,
                                                   "sumit_day_flag": sumit_day_flag,
                                                   "sumit_answered_today": sumit_answered_today,
                                                   "sumit_next_level": sumit_next_level,
                                                   "sumit_correct_answers": tempSCA,
                                                   "sumit_day": sumit_day,
                                                   "sumit": sumit,
                                                   "feedback_string": feedback_string,
                                                   "user": user})

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


@oneplus_participant_required
def nextchallenge(request, state, user, participant):
    # get learner state
    _participant = participant
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    # check if new question required then show question
    next_question = _learnerstate.getnextquestion()
    if not next_question:
        return redirect("learn.home")

    request.session["state"]["next_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count() + 1

    points = _learnerstate.active_question.points
    show_point = Setting.get_setting(key="SHOW_POINT_ALLOCATION")
    if show_point:
        if show_point != "True" or _learnerstate.active_question.points is None:
            points = ""

    golden_egg = {}

    if (len(_learnerstate.get_answers_this_week()) + _learnerstate.get_num_questions_answered_today() + 1) == \
            _learnerstate.golden_egg_question and get_golden_egg(_participant):
        if ((_learnerstate.golden_egg_question - 1) // 3) == _learnerstate.get_week_day():
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
            "module": _learnerstate.active_question.module,
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
            _learner_level_before, _threshold = _participant.calc_level()

            # Answer question
            _participant.answer(_option.question, _option)

            # Update metrics
            update_num_question_metric()

            try:
                update_all_perc_correct_answers.delay()
            except Exception as e:
                pass

            # Check for award

            if _option.correct:

                # Important
                _total_correct = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant,
                    correct=True
                ).count()

                if _total_correct == 1:
                    _participant.award_scenario(
                        "1_CORRECT",
                        _learnerstate.active_question.module,
                        special_rule=True
                    )

                if _total_correct == 15:
                    _participant.award_scenario(
                        "15_CORRECT",
                        _learnerstate.active_question.module,
                        special_rule=True
                    )

                if _total_correct == 30:
                    _participant.award_scenario(
                        "30_CORRECT",
                        _learnerstate.active_question.module,
                        special_rule=True
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
                    _participant.award_scenario(
                        "3_CORRECT_RUNNING",
                        _learnerstate.active_question.module,
                        special_rule=True
                    )

                last_5 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:5]

                if last_5.count() == 5 \
                        and len([i for i in last_5 if i.correct]) == 5:
                    _participant.award_scenario(
                        "5_CORRECT_RUNNING",
                        _learnerstate.active_question.module,
                        special_rule=True
                    )

                _learner_level_after, _threshold = _participant.calc_level()
                level_badge_names = ['Level {0:d}'.format(i) for i in xrange(1, settings.MAX_LEVEL + 1)]
                search_badges = level_badge_names[:_learner_level_after]

                badges_earned = GamificationBadgeTemplate.objects.filter(name__in=search_badges)\
                    .exclude(participantbadgetemplaterel__participant_id=participant.id)

                for badge in badges_earned:
                    _participant.award_scenario(
                        "LEVELED_TO_{0:s}".format(badge.name.split()[-1]),
                        _learnerstate.active_question.module,
                        special_rule=True
                    )

                return redirect("learn.right")

            else:
                return redirect("learn.wrong")
        else:
            return get()

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def redo(request, state, user, participant):
    # get learner state
    _participant = participant
    _learnerstate = LearnerState.objects.filter(
        participant__id=user["participant_id"]
    ).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    # check if new question required then show question
    redo_question = _learnerstate.get_next_redo_question()

    if not redo_question:
        return redirect("learn.home")

    redo_question_module = None

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        redo_question_module = _learnerstate.redo_question.module
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        done_count, total_count = _learnerstate.get_redo_question_count()
        return render(request, "learn/redo.html", {
            "points": redo_question.points,
            "question": _learnerstate.redo_question,
            "question_number": done_count + 1,
            "state": state,
            "module": redo_question_module,
            "question_total": total_count,
            "user": user,
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
            return get()

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def redo_right(request, state, user, participant):
    # get learner state
    _participant = participant
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    redo_count = _learnerstate.get_redo_questions().count()

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    questions = len(_learnerstate.get_redo_questions())

    _usr = Learner.objects.get(pk=user["id"])
    request.session["state"]["banned"] = _usr.is_banned()

    def retrieve_message_objects():
        return Discussion.objects.filter(course=_participant.classs.course,
                                         question=_learnerstate.redo_question,
                                         moderated=True,
                                         unmoderated_date=None,
                                         reply=None)\
            .annotate(like_count=Count('discussionlike__user'))

    def retrieve_popular_message_objects():
        return retrieve_message_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        if _learnerstate.active_redo_result:
            all_messages = retrieve_message_objects()
            request.session["state"]["discussion_page_max"] = all_messages.count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = all_messages.order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.like_count = DiscussionLike.count_likes(comment)
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/redo_right.html",
                {
                    "comment_messages": _messages,
                    "has_next": redo_count > 0,
                    "points": _learnerstate.redo_question.points if _learnerstate.redo_question else None,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.redo_question,
                    "questions": questions,
                    "state": state,
                    "user": user,
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.redo_right"))
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.redo_right"))
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

            elif "report" in request.POST.keys():
                post_comment = Discussion.objects.filter(id=request.POST.get("report")).first()
                if post_comment is not None:
                    report_user_post(post_comment, _usr, 1)
                return redirect(reverse("learn.redo_right"))

            elif "like" in request.POST.keys():
                discussion_id = request.POST["like"]
                comment = Discussion.objects.filter(id=discussion_id).first()
                if comment is not None:
                    if "has_liked" in request.POST.keys():
                        DiscussionLike.unlike(_usr, comment)
                    else:
                        DiscussionLike.like(_usr, comment)
                    return redirect("learn.redo_right")

            _messages = retrieve_message_objects()\
                .order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/redo_right.html",
                {
                    "comment_messages": _messages,
                    "has_next": redo_count > 0,
                    "points": _learnerstate.redo_question.points if _learnerstate.redo_question else None,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.redo_question,
                    "state": state,
                    "user": user,
                }
            )
        else:
            return HttpResponseRedirect("redo_wrong")

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def redo_wrong(request, state, user, participant):
    # get learner state
    _participant = participant
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    redo_count = _learnerstate.get_redo_questions().count()

    if _learnerstate.redo_question:
        question_id = _learnerstate.redo_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"
    questions = len(_learnerstate.get_redo_questions())

    _usr = Learner.objects.get(pk=user["id"])

    request.session["state"]["banned"] = _usr.is_banned()

    def retrieve_message_objects():
        return Discussion.objects.filter(course=_participant.classs.course,
                                         question=_learnerstate.redo_question,
                                         moderated=True,
                                         unmoderated_date=None,
                                         reply=None)\
            .annotate(like_count=Count('discussionlike__user'))

    def retrieve_popular_message_objects():
        return retrieve_message_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        if not _learnerstate.active_redo_result:
            all_messages = retrieve_message_objects()

            request.session["state"]["discussion_page_max"] = all_messages.count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = all_messages.order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/redo_wrong.html",
                {
                    "comment_messages": _messages,
                    "has_next": redo_count > 0,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.redo_question,
                    "questions": questions,
                    "state": state,
                    "user": user,
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.redo_wrong"))
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.redo_wrong"))
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

            elif "report" in request.POST.keys():
                post_comment = Discussion.objects.filter(id=request.POST.get("report")).first()
                if post_comment is not None:
                    report_user_post(post_comment, _usr, 1)
                return redirect(reverse("learn.redo_wrong"))

            elif "like" in request.POST.keys():
                discussion_id = request.POST["like"]
                comment = Discussion.objects.filter(id=discussion_id).first()
                if comment is not None:
                    if "has_liked" in request.POST.keys():
                        DiscussionLike.unlike(_usr, comment)
                    else:
                        DiscussionLike.like(_usr, comment)
                    return redirect("learn.redo_wrong")

            _messages = retrieve_message_objects()\
                .order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/redo_wrong.html",
                {
                    "comment_messages": _messages,
                    "has_next": redo_count > 0,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.redo_question,
                    "state": state,
                    "user": user,
                }
            )
        else:
            return HttpResponseRedirect("right")

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def event(request, state, user, participant):
    _participant = participant
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


@oneplus_participant_required
def event_right(request, state, user, participant):
    _participant = participant
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


@oneplus_participant_required
def event_wrong(request, state, user, participant):
    _participant = participant
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


@oneplus_participant_required
def sumit(request, state, user, participant):
    _participant = participant
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()
                                  ).first()

    if not _sumit:
        return redirect("learn.home")

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    if not EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).exists() or \
            _learnerstate.sumit_level not in range(1, 6) or \
            _learnerstate.sumit_question not in range(1, 4):
        _learnerstate.sumit_level = 1
        _learnerstate.sumit_question = 1
        _learnerstate.save()

    if not EventParticipantRel.objects.filter(event=_sumit, participant=_participant).exists():
        EventParticipantRel.objects.create(participant=_participant, event=_sumit, sitting_number=1)

    request.session["state"]["next_tasks_today"] = \
        EventQuestionAnswer.objects.filter(
            event=_sumit,
            participant=_participant,
            answer_date__gte=date.today()
        ).distinct('participant', 'question').count() + 1

    _question = _sumit.get_next_sumit_question(_participant, _learnerstate.sumit_level, _learnerstate.sumit_question)

    if not _question:
        return redirect("learn.home")

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
                "sumit": sumit,
                "count": _learnerstate.get_num_questions_answered_today() + 1,
                "total_questions": _learnerstate.get_questions_available_count
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


@oneplus_participant_required
def sumit_right(request, state, user, participant):
    _participant = participant
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()
    if not _sumit:
        return redirect("learn.home")

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()
    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    _question = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant) \
        .order_by("-answer_date").first().question

    request.session["state"]["right_tasks_today"] = \
        EventQuestionAnswer.objects.filter(event=_sumit,
                                           participant=_participant, answer_date__gte=date.today()
                                           ).distinct('participant', 'question').count()

    sumit = dict()
    sumit_question = _learnerstate.sumit_question

    temp_sumit_question = sumit_question
    if temp_sumit_question == 1:
        temp_sumit_question = 4
        sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level-1)
    else:
        sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level)

    sumit["level"] = sumit_level.name

    for i in range(1, 4):
        if i in range(1, temp_sumit_question):
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_04.png"
        else:
            sumit["url%d" % i] = "media/img/OP_SUMit_Question_0%d.png" % i

    num_sumit_questions = SUMitLevel.objects.all().count() * _learnerstate.QUESTIONS_PER_DAY
    num_sumit_questions_answered = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).count()

    sumit["finished"] = None
    if num_sumit_questions == num_sumit_questions_answered:
        sumit["finished"] = True

    level_up = False
    if temp_sumit_question == 4 and sumit["finished"] is None:
        level_up = True

    def get():
        return render(
            request,
            "learn/sumit_right.html",
            {
                "state": state,
                "user": user,
                "question": _question,
                "sumit": sumit,
                "level_up": level_up
            }
        )

    def post():
        return get()

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def sumit_level_up(request, state, user, participant):
    _participant = participant
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if not _sumit:
        return redirect("learn.home")

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()
    if _learnerstate is None:
        return redirect("learn.home")

    if _learnerstate.sumit_question != 1 and _learnerstate.sumit_level not in range(2, 4):
        return redirect("learn.home")

    previous_level = dict()
    next_level = dict()

    previous_level["name"] = SUMitLevel.objects.get(order=_learnerstate.sumit_level - 1).name
    next_level["name"] = SUMitLevel.objects.get(order=_learnerstate.sumit_level).name

    if _learnerstate.sumit_level == 2:
        previous_level["front_colour"] = "green-front"
        previous_level["back_colour"] = "green-back"
        next_level["colour"] = "yellow-front"
    elif _learnerstate.sumit_level == 3:
        previous_level["front_colour"] = "yellow-front"
        previous_level["back_colour"] = "yellow-back"
        next_level["colour"] = "purple-front"
    elif _learnerstate.sumit_level == 4:
        previous_level["front_colour"] = "purple-front"
        previous_level["back_colour"] = "purple-back"
        next_level["colour"] = "cyan-front"
    elif _learnerstate.sumit_level == 5:
        previous_level["front_colour"] = "cyan-front"
        previous_level["back_colour"] = "cyan-back"
        next_level["colour"] = "green-front"

    def get():
        return render(
            request,
            "learn/sumit_level_up.html",
            {
                "state": state,
                "user": user,
                "previous_level": previous_level,
                "next_level": next_level,
            }
        )

    return resolve_http_method(request, [get])


@oneplus_participant_required
def sumit_wrong(request, state, user, participant):
    _participant = participant
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if not _sumit:
        return redirect("learn.home")

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
    badges = ParticipantBadgeTemplateRel.objects.filter(
        participant=participant,
        badgetemplate__is_active=True,
        awarddate__range=[
            datetime.today() - timedelta(seconds=10),
            datetime.today()
        ]
    ).order_by('badgetemplate__name')

    return [{
        'badgetemplate': badge.badgetemplate,
        'badgepoints': GamificationScenario.objects.get(badge__id=badge.badgetemplate.id).point
    } for badge in badges]


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


@oneplus_participant_required
def right(request, state, user, participant):
    # get learner state
    _participant = participant
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

    if (len(_learnerstate.get_answers_this_week()) + _learnerstate.get_num_questions_answered_today()) == \
            _learnerstate.golden_egg_question and get_golden_egg(_participant):
        # ensure the question was answered on the allocated bucket day, 3 days per bucket
        # ie. golden_egg_question = 1 Only Monday
        #     golden_egg_question = 7 Only Wednesday
        if ((_learnerstate.golden_egg_question - 1) // 3) == _learnerstate.get_week_day():
            _golden_egg = get_golden_egg(_participant)
            if _golden_egg and "won_golden_egg" not in state:
                state["won_golden_egg"] = True
                if _golden_egg.point_value:
                    golden_egg["message"] = "You've won this week's Golden Egg and %d points." % _golden_egg.point_value
                    _participant.points += _golden_egg.point_value
                    _participant.save()
                if _golden_egg.airtime:
                    golden_egg["message"] = "You've won this week's Golden Egg and your share of R %d airtime. " \
                                            "You will be awarded your airtime next Monday." % _golden_egg.airtime
                    mail_managers(subject="Golden Egg Airtime Award",
                                  message="%s %s %s won R %d airtime from a Golden Egg"
                                          % (_participant.learner.first_name, _participant.learner.last_name,
                                             _participant.learner.mobile, _golden_egg.airtime),
                                  fail_silently=False)
                if _golden_egg.badge:
                    golden_egg["message"] = "You've won this week's Golden Egg and a badge"

                    b = ParticipantBadgeTemplateRel(participant=_participant,
                                                    badgetemplate=_golden_egg.badge.badge,
                                                    scenario=_golden_egg.badge,
                                                    awarddate=datetime.now())
                    b.save()

                    BadgeAwardLog(participant_badge_rel=b, award_date=datetime.now()).save()

                    if _golden_egg.badge.point and _golden_egg.badge.point.value:
                        _participant.points += _golden_egg.badge.point.value
                        _participant.save()

                golden_egg["url"] = Setting.objects.get(key="GOLDEN_EGG_IMG_URL").value
                GoldenEggRewardLog(participant=_participant,
                                   points=_golden_egg.point_value,
                                   airtime=_golden_egg.airtime,
                                   badge=_golden_egg.badge).save()

    state["total_tasks_today"] = _learnerstate.get_total_questions()

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    _usr = Learner.objects.get(pk=user["id"])
    request.session["state"]["banned"] = _usr.is_banned()

    def retrieve_comment_objects():
        return Discussion.objects.filter(course=_participant.classs.course,
                                         moderated=True,
                                         question=_learnerstate.active_question,
                                         unmoderated_date=None)\
            .annotate(like_count=Count('discussionlike__user'))

    def retrieve_popular_comment_objects():
        return retrieve_comment_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        if _learnerstate.active_result:
            all_messages = retrieve_comment_objects()

            request.session["state"]["discussion_page_max"] = all_messages.count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = all_messages.order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_comment_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            # Get badge points
            badge_objects = get_badge_awarded(_participant)
            badges = [badge['badgetemplate'] for badge in badge_objects]
            points = get_points_awarded(_participant) + get_event_points_awarded(_participant)
            return render(
                request,
                "learn/right.html",
                {
                    "badges": badges,
                    "comment_messages": _messages,
                    "golden_egg": golden_egg,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.active_question,
                    "points": points,
                    "state": state,
                    "user": user,
                },
                context_instance=RequestContext(request)
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.right"))

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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.save()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.right"))
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

            elif "report" in request.POST.keys():
                post_comment = Discussion.objects.filter(id=request.POST.get("report")).first()
                if post_comment is not None:
                    report_user_post(post_comment, _usr, 1)
                return redirect(reverse("learn.right"))

            elif "like" in request.POST.keys():
                discussion_id = request.POST["like"]
                comment = Discussion.objects.filter(id=discussion_id).first()
                if comment is not None:
                    if "has_liked" in request.POST.keys():
                        DiscussionLike.unlike(_usr, comment)
                    else:
                        DiscussionLike.like(_usr, comment)
                    return redirect("learn.right")

            _messages = retrieve_comment_objects()\
                .order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_comment_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/right.html",
                {
                    "comment_messages": _messages,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.active_question,
                    "state": state,
                    "user": user,
                }
            )
        else:
            return HttpResponseRedirect("wrong")

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def wrong(request, state, user, participant):
    # get learner state
    _participant = participant
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

    def retrieve_message_objects():
        return Discussion.objects.filter(course=_participant.classs.course,
                                         question=_learnerstate.active_question,
                                         moderated=True,
                                         unmoderated_date=None,
                                         reply=None)\
            .annotate(like_count=Count('discussionlike__user'))

    def retrieve_popular_message_objects():
        return retrieve_message_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        if not _learnerstate.active_result:
            all_messages = retrieve_message_objects()

            request.session["state"]["discussion_page_max"] = all_messages.count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = all_messages.order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            return render(
                request,
                "learn/wrong.html",
                {
                    "comment_messages": _messages,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.active_question,
                    "state": state,
                    "user": user,
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()

                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.wrong"))
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

                if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None
                return redirect(reverse("learn.wrong"))
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

            elif "report" in request.POST.keys():
                post_comment = Discussion.objects.filter(id=request.POST.get("report")).first()
                if post_comment is not None:
                    report_user_post(post_comment, _usr, 1)
                return redirect(reverse("learn.wrong"))

            elif "like" in request.POST.keys():
                discussion_id = request.POST["like"]
                comment = Discussion.objects.filter(id=discussion_id).first()
                if comment is not None:
                    if "has_liked" in request.POST.keys():
                        DiscussionLike.unlike(_usr, comment)
                    else:
                        DiscussionLike.like(_usr, comment)
                    return redirect("learn.wrong")

            _messages = retrieve_message_objects()\
                .order_by("-publishdate")[:request.session["state"]["discussion_page"]]
            _popular_messages = retrieve_popular_message_objects()[:2]

            for comment in _messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            for comment in _popular_messages:
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

            request.session["state"]["discussion_page_max"] = _messages.count()
            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            return render(
                request,
                "learn/wrong.html",
                {
                    "comment_messages": _messages,
                    "most_popular": _popular_messages,
                    "question": _learnerstate.active_question,
                    "state": state,
                    "user": user,
                }
            )
        else:
            return HttpResponseRedirect("right")

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def event_splash_page(request, state, user, participant):
    _participant = participant
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

    if _event.type == 0:
        badge_name = "Summit"
    elif _event.type == 1:
        badge_name = "Spot Test"
    else:
        badge_name = "Exam"

    try:
        badge_filename = GamificationBadgeTemplate.objects.get(name=badge_name).image
    except GamificationBadgeTemplate.DoesNotExist:
        badge_filename = None

    page["badge_filename"] = "media/%s" % badge_filename

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


@oneplus_participant_required
def event_start_page(request, state, user, participant):
    _participant = participant
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


@oneplus_participant_required
def event_end_page(request, state, user, participant):
    _participant = participant
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

        page["percentage"] = round(percentage)
        end_page = EventEndPage.objects.filter(event=_event).first()
        if end_page:
            page["heading"] = end_page.header
            page["message"] = end_page.paragraph

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
                module,
                special_rule=True
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
                module,
                special_rule=True
            )
    else:
        return redirect("learn.home")
    badge_objects = get_badge_awarded(_participant)
    badges = [badge['badgetemplate'] for badge in badge_objects]

    def get():
        return render(
            request,
            "learn/event_end_page.html",
            {
                "state": state,
                "user": user,
                "page": page,
                "badges": badges,
            }
        )

    return resolve_http_method(request, [get])


@oneplus_participant_required
def sumit_end_page(request, state, user, participant):
    _participant = participant
    _sumit = SUMit.objects.filter(course=_participant.classs.course,
                                  activation_date__lte=datetime.now(),
                                  deactivation_date__gt=datetime.now()).first()

    if not _sumit:
        return redirect("learn.home")

    rel = EventParticipantRel.objects.filter(event=_sumit, participant=_participant).first()

    if rel.results_received:
        return redirect("learn.home")

    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    page = {}
    sumit = dict()
    sumit["points"] = 0

    num_sumit_questions = SUMitLevel.objects.all().count() * _learnerstate.QUESTIONS_PER_DAY
    num_sumit_questions_answered = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant).count()

    if num_sumit_questions == num_sumit_questions_answered:
        if _learnerstate.sumit_level in range(1, 5):
            winner = False
        elif _learnerstate.sumit_level == 5:
            num_sumit_questions_correct = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant,
                                                                             correct=True).count()
            if num_sumit_questions_correct == num_sumit_questions:
                winner = True
                rel.winner = True
                rel.save()

                if _sumit.event_points:
                    sumit["points"] = _sumit.event_points
                    _participant.points += _sumit.event_points
                    rel.results_received = True
                    rel.save()

                if _sumit.airtime:
                    mail_managers(subject="SUMit! Airtime Award", message="%s %s %s won R %d airtime from an event"
                                                                          % (_participant.learner.first_name,
                                                                             _participant.learner.last_name,
                                                                             _participant.learner.mobile,
                                                                             _sumit.airtime), fail_silently=False)
                    sumit["airtime"] = _sumit.airtime

                if _sumit.event_badge:
                    module = CourseModuleRel.objects.filter(course=_sumit.course).first()
                    _participant.award_scenario(
                        _sumit.event_badge.event,
                        module,
                        special_rule=True
                    )
                _participant.save()

                mail_managers(subject="SUMit Winner!", message="%s %s %s won %s SUMit!"
                                                               % (_participant.learner.first_name,
                                                                  _participant.learner.last_name,
                                                                  _participant.learner.mobile,
                                                                  _sumit.name))
            else:
                winner = False

        rel.sumit_level = SUMitLevel.objects.get(order=_learnerstate.sumit_level).name
        rel.results_received = True
        rel.save()

        sumit["level"] = SUMitLevel.objects.get(order=_learnerstate.sumit_level).name
        points = EventQuestionAnswer.objects.filter(event=_sumit, participant=_participant, correct=True)\
            .aggregate(Sum('question__points'))['question__points__sum']
        sumit["points"] += points

        if sumit["level"] == 'Summit':
            front = "white-front"
            back = "darkgrey-back"
        elif sumit["level"] == "Peak":
            front = "darkgrey-front"
            back = "cyan-back"
        elif sumit["level"] == "Cliffs":
            front = "darkgrey-front"
            back = "purple-back"
        elif sumit["level"] == "Foothills":
            front = "darkgrey-front"
            back = "yellow-back"
        else:
            front = "darkgrey-front"
            back = "green-back"

    else:
        return redirect("learn.home")

    badge_objects = get_badge_awarded(_participant)
    badges = [badge['badgetemplate'] for badge in badge_objects]

    def get():
        return render(
            request,
            "learn/sumit_end_page.html",
            {
                "state": state,
                "user": user,
                "page": page,
                "badges": badges,
                "sumit": sumit,
                "front": front,
                "back": back,
                "winner": winner
            }
        )

    return resolve_http_method(request, [get])


@oneplus_participant_required
def report_question(request, state, user, participant, questionid, frm):
    _participant = participant
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

            for comment in _messages:
                comment.like_count = DiscussionLike.count_likes(comment)
                comment.has_liked = DiscussionLike.has_liked(_usr, comment)

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
