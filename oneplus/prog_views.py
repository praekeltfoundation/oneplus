from __future__ import division
from datetime import datetime, timedelta
from itertools import chain
from django.core.urlresolvers import reverse
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
    max_uncollapsed = 3

    # TODO: Move leaderboard functions to separate file.

    def get_class_leaderboard():
        eligible_participants = Participant.objects.filter(classs=_participant.classs, is_active=True, points__gt=0)

        position = eligible_participants.filter(points__gt=_participant.points).count() + 1

        scores = eligible_participants\
            .values('points')\
            .annotate(num_participants=Count('id'))\
            .distinct()\
            .order_by('-points')[:10]

        leaderboard = []
        for score in scores:
            more = False
            if score['num_participants'] >= max_uncollapsed:
                more = True

            if participant.points == score['points']:
                p_me = eligible_participants.filter(id=participant.id)\
                    .values('id', 'learner__first_name', 'learner__last_name')
                p_list = eligible_participants.filter(points=score['points'])\
                    .values('id', 'learner__first_name', 'learner__last_name')[:max_uncollapsed - 1]
                p_list = p_me | p_list
            else:
                p_list = eligible_participants.filter(points=score['points'])\
                    .values('id', 'learner__first_name', 'learner__last_name')[:max_uncollapsed]

            members = [{'me': (a['id'] == participant.id),
                        'name': "{0:s} {1:s}".format(a['learner__first_name'],
                                                     a['learner__last_name'])} for a in p_list]

            if len(members) > 0:
                members[0]['position'] = eligible_participants.filter(points__gt=score['points']).count() + 1

            leaderboard += [
                {'members': members,
                 'points': score['points']}]

        return {'board': leaderboard, 'position': position}

    def get_school_leaderboard():
        schools = School.objects.filter(learner__grade=_participant.learner.grade,
                                        learner__participant__is_active=True)\
            .values('id', 'name')\
            .distinct()\
            .annotate(points=Sum('learner__participant__points'))\
            .order_by('-points', 'name')\

        my_school = schools.get(id=participant.learner.school.id)
        position = schools.filter(points__gt=my_school['points']).count() + 1

        scores = schools\
            .values_list('points', flat=True)

        leaderboard = []
        for score in scores:
            more = False

            if my_school['points'] == score:
                p_me = schools.filter(id=participant.learner.school.id)\
                    .values('id', 'name', 'points')
                p_list = schools.filter(points=score)\
                    .exclude(id=participant.learner.school.id)\
                    .values('id', 'name', 'points')\
                    .order_by()[:max_uncollapsed - 1]
                p_list = list(chain(p_me, p_list))
            else:
                p_list = schools.filter(points=score)\
                    .values('id', 'name', 'points')[:max_uncollapsed + 1]
                if p_list.count() >= max_uncollapsed:
                    more = True
                    p_list = p_list[:-1]

            members = [{'me': (a['id'] == participant.learner.school.id),
                        'name': a['name']} for a in p_list]

            if len(members) > 0:
                members[0]['position'] = schools.filter(points__gt=score).count() + 1

            leaderboard += [
                {'members': members,
                 'points': score}]

        return {'board': leaderboard, 'position': position}

    def get_national_leaderboard():
        eligible_participants = Participant.objects.filter(learner__grade=_participant.learner.grade,
                                                           is_active=True,
                                                           points__gt=0)

        position = eligible_participants.filter(points__gt=_participant.points).count() + 1

        scores = eligible_participants\
            .values('points')\
            .annotate(num_participants=Count('id'))\
            .distinct()\
            .order_by('-points')[:10]

        leaderboard = []
        for score in scores:
            more = False
            if score['num_participants'] >= max_uncollapsed:
                more = True

            if participant.points == score['points']:
                p_me = eligible_participants.filter(id=participant.id)\
                    .values('id',
                            'learner__first_name',
                            'learner__last_name',
                            'learner__school__name')
                p_list = eligible_participants.filter(points=score['points'])\
                    .values('id',
                            'learner__first_name',
                            'learner__last_name',
                            'learner__school__name')[:max_uncollapsed - 1]
                p_list = p_me | p_list
            else:
                p_list = eligible_participants.filter(points=score['points'])\
                    .values('id', 'learner__first_name',
                            'learner__last_name',
                            'learner__school__name')[:max_uncollapsed]

            members = [{'me': (a['id'] == participant.id),
                        'name': "{0:s} {1:s}".format(a['learner__first_name'],
                                                     a['learner__last_name']),
                        'school': a['learner__school__name']} for a in p_list]

            if len(members) > 0:
                members[0]['position'] = eligible_participants.filter(points__gt=score['points']).count() + 1

            leaderboard += [
                {'members': members,
                 'points': score['points']}]

        return {'board': leaderboard, 'position': position}

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
def badges(request, state, user, participant, badge_id=None):
    # get learner state
    if badge_id and unicode.isdigit(badge_id):
        badge_id = int(badge_id)
    else:
        badge_id = None
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
        if badge_id:
            for b in _badges:
                if b.id == badge_id:
                    share_url = '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'),
                                                               participant.id,
                                                               badge_id)
                    return render(request, "prog/badge_single.html", {
                        "badge": b,
                        "participant": _participant,
                        "share_url": share_url,
                        "state": state,
                        "user": user})
            return redirect('prog.badges')

        return render(request, "prog/badges.html", {
            "state": state,
            "user": user,
            "badges": _badges,
            "participant": _participant
        })

    def post():
        return get()

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
