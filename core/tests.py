from django.test import TestCase
from datetime import datetime
from auth.models import Learner
from organisation.models import Course, Module, School, Organisation
from core.models import Participant, Class, ParticipantBadgeTemplateRel
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario


class TestMessage(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_module(self, name, course, **kwargs):
        return Module.objects.create(name=name, course=course, **kwargs)

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(
            name=name,
            organisation=organisation,
            **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(
            learner=learner,
            classs=classs,
            **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(name=name, **kwargs)

    def create_pointbonus(self, name='point bonus name', **kwargs):
        return GamificationPointBonus.objects.create(name=name, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module name', self.course)
        self.classs = self.create_class('class name', self.course)

        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            mobile="+27123456789",
            country="country")

        self.badge_template = self.create_badgetemplate()

        # create point bonus with value 5
        self.pointbonus = self.create_pointbonus(value=5)

        # create scenario
        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='event name',
            course=self.course,
            module=self.module,
            point=self.pointbonus,
            badge=self.badge_template
        )

        # create scenario
        self.scenario_no_module = GamificationScenario.objects.create(
            name='scenario name no module',
            event='event name no module',
            course=self.course,
            module=None,
            point=self.pointbonus,
            badge=self.badge_template
        )

    def test_award_scenario(self):
        participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

        # participant should have 0 points
        self.assertEquals(0, participant.points)

        # award points to participant
        participant.award_scenario('event name', self.module)
        participant.save()

        # participant should have 5 points
        self.assertEquals(5, participant.points)

        # check badge was awarded
        b = ParticipantBadgeTemplateRel.objects.get(participant=participant)
        self.assertTrue(b.awarddate)

    def test_award_scenario_none_module(self):
        participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

        # participant should have 0 points
        self.assertEquals(0, participant.points)

        # award points to participant
        participant.award_scenario('event name no module', None)
        participant.save()

        # participant should have 5 points
        self.assertEquals(5, participant.points)

        # check badge was awarded
        b = ParticipantBadgeTemplateRel.objects.get(participant=participant)
        self.assertTrue(b.awarddate)
