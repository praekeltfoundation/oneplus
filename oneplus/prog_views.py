from __future__ import division
from datetime import datetime, timedelta

from django.shortcuts import render
from django.db.models import Count
from django.shortcuts import render
from django.db.models import Count
from auth.models import Learner
from core.models import Participant, ParticipantQuestionAnswer, Class, ParticipantBadgeTemplateRel
from gamification.models import GamificationScenario
from oneplus.views import oneplus_state_required, oneplus_login_required, COUNTRYWIDE
from oneplus.auth_views import resolve_http_method


@oneplus_state_required
@oneplus_login_required
def ontrack(request, state, user):
    # get on track state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _modules = Participant.objects.get(
        pk=user["participant_id"]).classs.course.modules.all().order_by('order')

    # Calculate achieved score
    for m in _modules:
        _answers = _participant.participantquestionanswer_set.filter(
            question__module__id=m.id)
        if _answers.count() < 10:
            m.score = -1
        else:
            m.score = _answers.filter(
                correct=True
            ).count() / _answers.count() * 100

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


@oneplus_state_required
@oneplus_login_required
def leader(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])

    def get_overall_leaderboard():
        leaderboard = Participant.objects.filter(classs=_participant.classs,) \
            .order_by("-points", 'learner__first_name')

        learners = []
        position = None
        i = 0
        for a in leaderboard:
            i += 1
            learner = {"id": a.id, "name": a.learner.first_name, "points": a.points, "position": i}
            if a.id == _participant.id:
                learner['me'] = True
                position = i
            learners.append(learner)

            if position is not None and i >= 10:
                break

        if position > 10 or position is None:
            learner = {"id": _participant.id, "name": _participant.learner.first_name, "points": _participant.points,
                       "me": True, "position": position}
            learners.insert(11, learner)
            return learners[:11], position
        else:
            return learners[:10], position

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
            learners.insert(11, _learner)
            return learners[:11], position
        else:
            return learners[:10], position

    def get_correct(answered_list, class_name):
        for l in answered_list:
            if l['participant__classs__name'] == class_name:
                return l
        return None

    def get_class_leaderboard():
        total_list = ParticipantQuestionAnswer.objects.values('participant__classs__name', ) \
            .annotate(answered=Count('question')) \
            .order_by('participant__classs')

        correct_list = ParticipantQuestionAnswer.objects.values('participant__classs__name') \
            .annotate(cor=Count('question')) \
            .filter(correct=True) \
            .order_by('participant__classs')

        classes = []
        position = None
        position_counter = 0
        name_list = []

        for tl in total_list:
            position_counter += 1
            cl = get_correct(correct_list, tl['participant__classs__name'])
            percent = '-'
            if cl:
                name_list.append(cl['participant__classs__name'])
                percent = str(int((cl['cor']) / int(tl['answered']) * 100)) + '%'

            classs = {"name": tl['participant__classs__name'], "points": percent}
            if _participant.classs.name == tl['participant__classs__name']:
                position = position_counter
                classs['me'] = True
            classes.append(classs)

        classes = sorted(classes, key=lambda k: k['points'])

        a = 0
        temp = []
        for classs in classes:
            a += 1
            classs['position'] = a
            temp.append(classs)

        classes = temp

        if len(classes) < 10:
            no_points_list = Class.objects.exclude(name__in=name_list).order_by('name')[:10 - len(classes)]

            if not position:
                temp_counter = position_counter
                for _l in no_points_list:
                    temp_counter += 1
                    if _participant.classs.name == _l.name:
                        position = temp_counter
                        break

            no_points_list = no_points_list[:10 - len(classes)]

            for _l in no_points_list:
                position_counter += 1
                classs = {"id": _l.id, "name": _l.name, "points": '-', "position": position_counter}
                if _participant.classs.name == _l.name:
                    classs['me'] = True
                classes.append(classs)

        if position > 10:
            classs = {"me": True, "name": tl['participant__classs__name'], "points": '-', "position": position}
            classes.insert(11, classs)
            return classes[:11], position
        else:
            return classes[:10], position

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
        request.session["state"]["leader_menu"] = False

        # Get leaderboard and position
        _learners, position = get_overall_leaderboard()

        return render(
            request,
            "prog/leader.html",
            {
                "state": state,
                "user": user,
                "learners": _learners,
                "position": position,
                "buttons": get_buttons("overall"),
                "header_1": "Leaderboard",
                "header_2": "Well done you're in "
            }
        )

    def post():
        buttons = get_buttons("overall")
        _learners, position = get_overall_leaderboard()
        header_1 = "Leaderboard"
        header_2 = "Well done you're in "

        # show region menu?
        if "leader_menu" in request.POST:
            request.session["state"]["leader_menu"] \
                = request.POST["leader_menu"] != 'True'

        elif "region" in request.POST:
            request.session["state"]["leader_menu"] = False
            request.session["state"]["leader_region"] = request.POST["region"]

        elif "overall" in request.POST:
            buttons = get_buttons("overall")
            _learners, position = get_overall_leaderboard()
            header_1 = "Leaderboard"
            header_2 = "Well done you're in "

        elif "two_week" in request.POST:
            buttons = get_buttons("two_week")
            _learners, position = get_weeks_leaderboard(2)
            header_1 = "2 Week Leaderboard"
            header_2 = "In the last 2 weeks, you're in"

        elif "three_month" in request.POST:
            buttons = get_buttons("three_month")
            _learners, position = get_weeks_leaderboard(12)
            header_1 = "3 Month Leaderboard"
            header_2 = "In the last 3 months, you're in"

        elif "class" in request.POST:
            buttons = get_buttons("class")
            _learners, position = get_class_leaderboard()
            header_1 = "Class Leaderboard"
            header_2 = "%s, you're in" % _participant.classs.name

        # Get unique regions
        request.session["state"]["leader_regions"] \
            = list([{"area": COUNTRYWIDE}]) \
            + list(Learner.objects.values("area").distinct().all())

        return render(
            request,
            "prog/leader.html",
            {
                "state": state,
                "user": user,
                "learners": _learners,
                "position": position,
                "buttons": buttons,
                "header_1": header_1,
                "header_2": header_2
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_state_required
@oneplus_login_required
def points(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _modules = _participant.classs.course.modules.all().order_by('order')
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


@oneplus_state_required
@oneplus_login_required
def badges(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = _participant.classs.course
    _allscenarios = GamificationScenario.objects.exclude(badge__isnull=True)\
        .filter(course=_course).prefetch_related("badge").order_by('badge__order')
    _badges = [scenario.badge for scenario in _allscenarios]

    # Link achieved badges
    for x in _badges:
        if ParticipantBadgeTemplateRel.objects.filter(
                participant=_participant,
                badgetemplate=x
        ).exists():
            x.achieved = True

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
