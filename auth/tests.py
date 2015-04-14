from django.test import TestCase
from datetime import datetime, timedelta
from auth.models import Learner
from organisation.models import (Course, Module, School, Organisation,
                                 CourseModuleRel)
from core.models import (Participant, Class, ParticipantQuestionAnswer)
from gamification.models import (GamificationBadgeTemplate,
                                 GamificationPointBonus,
                                 GamificationScenario)
from content.models import TestingQuestion, TestingQuestionOption
from auth.stats import *


class TestAuth(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course,module=module)
        module.save()
        rel.save()
        return module

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

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
            country="country",
            last_active_date=datetime.now())
        self.badge_template = self.create_badgetemplate()
        self.question = self.create_test_question('q1', self.module)
        self.option = self.create_test_question_option('opt_1', self.question)

        # create point bonus with value 5
        self.pointbonus = self.create_pointbonus(value=5)

        # create scenario
        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='test',
            course=self.course,
            module=self.module,
            point=self.pointbonus,
            badge=self.badge_template
        )
        self.participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

    def test_learners_active_in_last_x_hours(self):
        count = learners_active_in_last_x_hours(hours=24)
        self.assertEquals(count, 1)

        self.learner.last_active_date = datetime.now() - timedelta(days=2)
        self.learner.save()

        count = learners_active_in_last_x_hours(hours=24)
        self.assertEquals(count, 0)

        count = learners_active_in_last_x_hours(hours=49)
        self.assertEquals(count, 1)

    def test_total_active_learners(self):
        count = total_active_learners()
        self.assertEquals(count, 1)

        self.learner.is_active = False
        self.learner.save()
        count = total_active_learners()
        self.assertEquals(count, 0)

    def test_perc_sms_optin(self):
        perc = percentage_learner_sms_opt_ins()
        count = number_learner_sms_opt_ins()
        self.assertEquals(perc, 0)
        self.assertEquals(count, 0)

        self.learner.optin_sms = True
        self.learner.save()
        perc = percentage_learner_sms_opt_ins()
        count = number_learner_sms_opt_ins()
        self.assertEquals(perc, 100)
        self.assertEquals(count, 1)

    def test_perc_email_optin(self):
        perc = percentage_learner_email_opt_ins()
        count = number_learner_email_opt_ins()
        self.assertEquals(perc, 0)
        self.assertEquals(count, 0)

        self.learner.optin_email = True
        self.learner.save()
        perc = percentage_learner_email_opt_ins()
        count = number_learner_email_opt_ins()
        self.assertEquals(perc, 100)
        self.assertEquals(count, 1)