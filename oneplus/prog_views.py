from __future__ import division
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from auth.models import Learner
from organisation.models import School
from core.models import Participant, ParticipantQuestionAnswer, Class, ParticipantBadgeTemplateRel
from gamification.models import GamificationScenario
from oneplus.views import oneplus_participant_required, COUNTRYWIDE
from oneplus.auth_views import resolve_http_method
from django.contrib.auth.decorators import user_passes_test


@oneplus_participant_required
def ontrack(request, state, user, participant):
    # get on track state
    _participant = participant
    _modules = Participant.objects.get(
        pk=user["participant_id"]).classs.course.modules.filter(type=1).order_by('order')

    # Calculate achieved score
    for m in _modules:
        _answers = _participant.participantquestionanswer_set.filter(
            question__module__id=m.id)
        _redo_answers = _participant.participantquestionanswer_set.filter(
            question__module__id=m.id)
        if (_answers.count() + _redo_answers.count()) < 10:
            m.score = -1
        else:
            correct = _answers.filter(correct=True).count() + _redo_answers.filter(correct=True).count()
            total = _answers.count() + _redo_answers.count()
            m.score = correct / total * 100

    def get():
        return render(
            request,
            "prog/ontrack.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    def post():
        return render(
            request,
            "prog/ontrack.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def leader(request, state, user, participant):
    # get learner state
    _participant = participant

    def get_class_leaderboard():
        leaderboard = Participant.objects.filter(classs=_participant.classs, is_active=True) \
            .order_by("-points", 'learner__first_name')

        learners = []
        position = None
        position_counter = 0
        for a in leaderboard:
            position_counter += 1
            learner = {
                "id": a.id,
                "name": "%s %s" % (a.learner.first_name, a.learner.last_name),
                "position": position_counter}
            if a.id == _participant.id:
                learner['me'] = True
                position = position_counter
            learners.append(learner)

            if position is not None and position_counter >= 10:
                break

        return {'board': learners[:10], 'position': position}

    def get_school_leaderboard():
        leaderboard = Participant.objects.filter(learner__grade=_participant.learner.grade, is_active=True)\
            .values('learner__school_id', 'learner__school__name', 'points')\
            .annotate(school_points=Sum('points'))\
            .order_by('-school_points', 'learner__school__name')

        schools = []
        position = None
        position_counter = 0
        for a in leaderboard:
            position_counter += 1
            school = {
                "id": a['learner__school_id'],
                "name": a['learner__school__name'],
                "position": position_counter}
            if a['learner__school_id'] == _participant.learner.school_id:
                school['me'] = True
                position = position_counter
            schools.append(school)

            if position is not None and position_counter >= 10:
                break

        return {'board': schools[:10], 'position': position}

    def get_national_leaderboard():
        leaderboard = Participant.objects.filter(learner__grade=_participant.learner.grade, is_active=True) \
            .order_by("-points", 'learner__first_name')

        learners = []
        position = None
        position_counter = 0
        for a in leaderboard:
            position_counter += 1
            learner = {
                "id": a.id,
                "name": "%s %s" % (a.learner.first_name, a.learner.last_name),
                "position": position_counter}
            if a.id == _participant.id:
                learner['me'] = True
                position = position_counter
            learners.append(learner)

            if position is not None and position_counter >= 10:
                break

        return {'board': learners[:10], 'position': position}

    def get_weeks_leaderboard(weeks):
        leaderboard = ParticipantQuestionAnswer.objects.values('participant__id', 'participant__learner__first_name') \
            .annotate(points=Sum('question__points')) \
            .filter(answerdate__range=[datetime.now() - timedelta(weeks=weeks), datetime.now()],
                    correct=True,
                    participant__classs=_participant.classs) \
            .order_by('-points', 'participant__learner__first_name')

        learners = []
        position = None
        position_counter = 0
        id_list = []

        for _l in leaderboard:
            position_counter += 1
            _learner = {"id": _l['participant__id'], "name": _l['participant__learner__first_name'],
                        "points": _l['points'], "position": position_counter}

            if _participant.id == _l['participant__id']:
                position = position_counter
                _learner['me'] = True

            id_list.append(_l['participant__id'])
            learners.append(_learner)

        if len(leaderboard) < 10:
            no_points_list = Participant.objects.filter(classs=_participant.classs) \
                .exclude(id__in=id_list) \
                .order_by('learner__first_name')

            if not position:
                temp_counter = position_counter
                for _l in no_points_list:
                    temp_counter += 1
                    if _participant.id == _l.id:
                        position = temp_counter
                        break

            no_points_list = no_points_list[:10 - len(leaderboard)]

            for _l in no_points_list:
                position_counter += 1
                _learner = {"id": _l.id, "name": _l.learner.first_name, "points": 0, "position": position_counter}
                if _participant.id == _l.id:
                    _learner['me'] = True
                learners.append(_learner)

                if len(learners) >= 10:
                    break

        if position > 10:
            _learner = {"id": _participant.id, "name": _participant.learner.first_name, "points": 0, 'me': True,
                        "position": position}
            learners.insert(10, _learner)
            return learners[:11], position
        else:
            return learners[:10], position

    def get_buttons(button_name):
        buttons = []
        overall = {"name": "overall", "value": "Overall Leaderboard"}
        two_week = {"name": "two_week", "value": "2 Week Leaderboard"}
        three_month = {"name": "three_month", "value": "3 Month Leaderboard"}
        classs = {"name": "class", "value": "Class Leaderboard"}

        if button_name != "overall":
            buttons.append(overall)
        if button_name != "two_week":
            buttons.append(two_week)
        if button_name != "three_month":
            buttons.append(three_month)
        if button_name != "class":
            buttons.append(classs)

        return buttons

    def get():
        # Get leaderboard and position
        class_board = get_class_leaderboard()
        school_board = get_school_leaderboard()
        national_board = get_national_leaderboard()

        class_board['active'] = request.session.get('leader_class_active', None)
        school_board['active'] = request.session.get('leader_school_active', None)
        national_board['active'] = request.session.get('leader_national_active', None)

        return render(
            request,
            "prog/leader.html",
            {
                "state": state,
                "user": user,
                "class_board": class_board,
                "school_board": school_board,
                "national_board": national_board,
                "buttons": get_buttons("overall"),
                "header_1": "Leaderboard",
                "header_2": "Well done you're in "
            }
        )

    def post():
        request.session["state"]["leader_menu"] = False

        # Get leaderboard and position
        class_board = get_class_leaderboard()
        school_board = get_school_leaderboard()
        national_board = get_national_leaderboard()

        if 'board.class.active' in request.POST:
            if request.POST['board.class.active'] == 'true':
                request.session['leader_class_active'] = True
            else:
                request.session['leader_class_active'] = False

        if 'board.school.active' in request.POST:
            if request.POST['board.school.active'] == 'true':
                request.session['leader_school_active'] = True
            else:
                request.session['leader_school_active'] = False

        if 'board.national.active' in request.POST:
            if request.POST['board.national.active'] == 'true':
                request.session['leader_national_active'] = True
            else:
                request.session['leader_national_active'] = False

        class_board['active'] = request.session.get('leader_class_active', None)
        school_board['active'] = request.session.get('leader_school_active', None)
        national_board['active'] = request.session.get('leader_national_active', None)

        return render(
            request,
            "prog/leader.html",
            {
                "state": state,
                "user": user,
                "class_board": class_board,
                "school_board": school_board,
                "national_board": national_board,
                "buttons": get_buttons("overall"),
                "header_1": "Leaderboard",
                "header_2": "Well done you're in "
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def points(request, state, user, participant):
    _participant = participant
    _modules = _participant.classs.course.modules.filter(type=1).order_by('order')
    request.session["state"]["points_points"] = _participant.points

    def get_points_per_module():
        for m in _modules:
            answers = ParticipantQuestionAnswer.objects.filter(
                participant=_participant,
                question__module=m,
                correct=True
            )
            module_points = 0
            for answer in answers:
                module_points += answer.question.points

            m.score = module_points

    def get():
        get_points_per_module()
        return render(
            request,
            "prog/points.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    def post():
        get_points_per_module()
        return render(
            request,
            "prog/points.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def badges(request, state, user, participant):
    # get learner state
    _participant = participant
    _course = _participant.classs.course
    _allscenarios = GamificationScenario.objects.exclude(badge__isnull=True)\
        .filter(course=_course).prefetch_related("badge").order_by('badge__order')
    _badges = [scenario.badge for scenario in _allscenarios]

    # There are badges not linked to course or module, like Spot Test Champ, Exam Champ, etc.
    # this fetches them and allows the user to see them.
    _otherscenarios = GamificationScenario.objects.exclude(badge__isnull=True)\
        .filter(course__isnull=True, module__isnull=True).prefetch_related("badge").order_by('badge__order')
    _badges += [scenario.badge for scenario in _otherscenarios]

    # Link achieved badges
    for x in _badges:
        rel = ParticipantBadgeTemplateRel.objects.filter(participant=_participant, badgetemplate=x)
        if rel.exists():
            x.achieved = True
            x.count = rel.first().awardcount

    def get():
        return render(request, "prog/badges.html", {
            "state": state,
            "user": user,
            "badges": _badges,
            "participant": _participant
        })

    def post():
        return render(
            request,
            "prog/badges.html",
            {
                "state": state,
                "user": user,
                "badges": _badges,
                "participant": _participant
            }
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def award_badge(request, learner_id, scenario_id):
    try:
        participant = Participant.objects.get(learner__id=learner_id, is_active=True)
    except Participant.DoesNotExist:
        return redirect("/admin/auth/learner")

    try:
        scenario = GamificationScenario.objects.get(id=scenario_id)
    except GamificationScenario.DoesNotExist:
        return redirect("/admin/auth/learner")

    awarding_scenario = ParticipantBadgeTemplateRel.objects.filter(participant=participant,
                                                                   participant__is_active=True,
                                                                   scenario=scenario).first()

    allowed = True
    if awarding_scenario:
        if awarding_scenario.scenario.award_type == 1:
            allowed = False

    def get():
        return render(request,
                      "admin/auth/badge_award.html",
                      {
                          "allowed": allowed,
                          "participant": participant,
                          "scenario": scenario
                      })

    def post():
        if "award_yes" in request.POST.keys():
            if awarding_scenario:
                if allowed:
                    awarding_scenario.awardcount += 1
                    awarding_scenario.save()
                else:
                    return redirect("/admin/auth/learner/%s" % participant.learner.id)
            else:
                ParticipantBadgeTemplateRel.objects.create(participant=participant,
                                                           badgetemplate=scenario.badge,
                                                           scenario=scenario,
                                                           awarddate=datetime.now(),
                                                           awardcount=1)

        return redirect("/admin/auth/learner/%s" % participant.learner.id)

    return resolve_http_method(request, [get, post])
