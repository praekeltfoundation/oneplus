from django.test import TestCase
from django.test.utils import override_settings
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from core.models import Class, Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel
from content.models import TestingQuestion, TestingQuestionOption
from django.core.urlresolvers import reverse
from datetime import datetime, timedelta
from auth.models import Learner
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    if 'terms_accept' not in kwargs:
        kwargs['terms_accept'] = True
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)
    return participant


def create_badgetemplate(name='badge template name', **kwargs):
    return GamificationBadgeTemplate.objects.create(
        name=name,
        image="none",
        **kwargs)


def create_gamification_point_bonus(name, value, **kwargs):
    return GamificationPointBonus.objects.create(
        name=name,
        value=value,
        **kwargs)


def create_gamification_scenario(**kwargs):
    return GamificationScenario.objects.create(**kwargs)


def create_test_question_option(name, question, correct=True):
    return TestingQuestionOption.objects.create(
        name=name, question=question, correct=correct)


def create_test_answer(
        participant,
        question,
        option_selected,
        answerdate):
    return ParticipantQuestionAnswer.objects.create(
        participant=participant,
        question=question,
        option_selected=option_selected,
        answerdate=answerdate,
        correct=False
    )


@override_settings(VUMI_GO_FAKE=True)
class TestBadgeAwarding(TestCase):

    def setUp(self):

        self.course = create_course()
        self.classs = create_class('class name', self.course)
        self.organisation = create_organisation()
        self.school = create_school('school name', self.organisation)
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)
        self.badge_template = create_badgetemplate()

        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='1_CORRECT',
            course=self.course,
            module=self.module,
            badge=self.badge_template
        )

    def test_badge_awarding(self):
        new_learner = create_learner(self.school,
                                     username="+27123456999",
                                     mobile="+2712345699",
                                     unique_token='xyz',
                                     unique_token_expiry=datetime.now() + timedelta(days=30))

        new_participant = create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

        ten = 10
        gpb1 = create_gamification_point_bonus("Point Bonus", ten)

        # create the badges we want to win
        bt1 = create_badgetemplate(
            name="1st Correct",
            description="1st Correct"
        )

        bt2 = create_badgetemplate(
            name="15 Correct",
            description="15 Correct"
        )

        bt3 = create_badgetemplate(
            name="30 Correct",
            description="30 Correct"
        )

        bt4 = create_badgetemplate(
            name="100 Correct",
            description="100 Correct"
        )

        sc1 = create_gamification_scenario(
            name="1st correct",
            course=self.course,
            module=self.module,
            badge=bt1,
            event="1_CORRECT",
            point=gpb1
        )

        sc2 = create_gamification_scenario(
            name="15 correct",
            course=self.course,
            module=self.module,
            badge=bt2,
            event="15_CORRECT",
        )

        sc3 = create_gamification_scenario(
            name="30 correct",
            course=self.course,
            module=self.module,
            badge=bt3,
            event="30_CORRECT",
        )

        sc4 = create_gamification_scenario(
            name="100 correct",
            course=self.course,
            module=self.module,
            badge=bt4,
            event="100_CORRECT",
        )

        fifteen = 15
        for i in range(0, fifteen):
            question = create_test_question('q_15_%s' % i, self.module, question_content='test question', state=3)
            question_option = create_test_question_option('q_15_%s_O_1' % i, question)
            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(participant=new_participant,
                                                                  correct=True).count()

        participant = Participant.objects.get(id=new_participant.id)
        self.assertEquals(participant.points, ten + fifteen)

        self.assertEquals(fifteen, _total_correct)

        thirty = 30
        for i in range(fifteen, thirty):
            question = create_test_question('q_30_%s' % i,
                                            self.module,
                                            question_content='test question',
                                            state=3)

            question_option = create_test_question_option('q_30_%s_O_1' % i, question)

            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(
            participant=new_participant,
            correct=True
        ).count()

        self.assertEquals(thirty, _total_correct)

        hundred = 100
        for i in range(thirty, hundred):
            question = create_test_question('q_100_%s' % i, self.module, question_content='test question', state=3)

            question_option = create_test_question_option('q_100_%s_O_1' % i, question)

            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(
            participant=new_participant,
            correct=True
        ).count()

        self.assertEquals(hundred, _total_correct)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt1,
            scenario=sc1
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt2,
            scenario=sc2
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt3,
            scenario=sc3
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt4,
            scenario=sc4
        ).count()
        self.assertEquals(cnt, 1)

    def test_badge_awarding_2(self):
        new_learner = create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699",
            unique_token='xyz',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        new_participant = create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

        # create the badges we want to win
        bt1 = create_badgetemplate(
            name="15 Correct",
            description="15 Correct"
        )

        bt2 = create_badgetemplate(
            name="30 Correct",
            description="30 Correct"
        )

        bt3 = create_badgetemplate(
            name="100 Correct",
            description="100 Correct"
        )

        sc1 = create_gamification_scenario(
            name="15 correct",
            course=self.course,
            module=self.module,
            badge=bt1,
            event="15_CORRECT",
        )

        sc2 = create_gamification_scenario(
            name="30 correct",
            course=self.course,
            module=self.module,
            badge=bt2,
            event="30_CORRECT",
        )

        sc3 = create_gamification_scenario(
            name="100 correct",
            course=self.course,
            module=self.module,
            badge=bt3,
            event="100_CORRECT",
        )

        fifteen = 14
        for i in range(0, fifteen):
            question = create_test_question('q_15_%s' % i, self.module, question_content='test question', state=3)
            question_option = create_test_question_option('q_15_%s_O_1' % i, question)
            new_participant.answer(question, question_option)

        question = create_test_question('q_15_16', self.module, question_content='test question', state=3)
        question_option = create_test_question_option('q_15_16_O_1', question)
        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt1, scenario=sc1).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt1, scenario=sc1).count()
        self.assertEquals(cnt, 1)

        thirty = 29
        for i in range(fifteen + 1, thirty):
            question = create_test_question('q_30_%s' % i, self.module, question_content='test question', state=3)
            question_option = create_test_question_option('q_30_%s_O_1' % i, question)
            new_participant.answer(question, question_option)

        question = create_test_question('q_30_31', self.module, question_content='test question', state=3)
        question_option = create_test_question_option('q_30_31_O_1', question)
        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt2, scenario=sc2).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt2, scenario=sc2).count()
        self.assertEquals(cnt, 1)

        hundred = 99
        for i in range(thirty + 1, hundred):
            question = create_test_question('q_100_%s' % i, self.module, question_content='test question', state=3)
            question_option = create_test_question_option('q_100_%s_O_1' % i, question)
            new_participant.answer(question, question_option)

        question = create_test_question('q_100_101', self.module, question_content='test question', state=3)
        question_option = create_test_question_option('q_100_101_O_1', question)

        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt3, scenario=sc3).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(participant=new_participant,
                                                         badgetemplate=bt3, scenario=sc3).count()
        self.assertEquals(cnt, 1)
