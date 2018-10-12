from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from auth.models import Learner
from core.common import PROVINCES
from core.models import Class, Participant
from oneplus.validators import validate_mobile, validate_sign_up_form, validate_sign_up_form_normal, \
    validate_sign_up_form_school_confirm, validate_accept_terms_form
from datetime import datetime, timedelta
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    if 'accept_terms' not in kwargs:
        kwargs['terms_accept'] = True
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)
    return participant


@override_settings(JUNEBUG_FAKE=True)
class ValidatorTests(TestCase):

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
                is_staff=False,
                terms_accept=False)
            self.participant = create_participant(
                self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
            self.module = create_module('module name', self.course)

    def test_validate_mobile(self):
        v_mobile_1 = "0721234567"
        v_mobile_1 = validate_mobile(v_mobile_1)
        self.assertEquals(v_mobile_1, "0721234567")

        v_mobile_2 = "+27721234569"
        v_mobile_2 = validate_mobile(v_mobile_2)
        self.assertEquals(v_mobile_2, "+27721234569")

        v_mobile_3 = "+123721234567"
        v_mobile_3 = validate_mobile(v_mobile_3)
        self.assertEquals(v_mobile_3, "+123721234567")

        i_mobile_1 = "072123456"
        i_mobile_1 = validate_mobile(i_mobile_1)
        self.assertEquals(i_mobile_1, None)

        i_mobile_2 = "07212345678"
        i_mobile_2 = validate_mobile(i_mobile_2)
        self.assertEquals(i_mobile_2, None)

        i_mobile_3 = "+2821234567"
        i_mobile_3 = validate_mobile(i_mobile_3)
        self.assertEquals(i_mobile_3, None)

        i_mobile_4 = "+1237212345678"
        i_mobile_4 = validate_mobile(i_mobile_4)
        self.assertEquals(i_mobile_4, None)

    def test_validate_sign_up_form(self):
        # Test no data
        req = {}
        data, errors = validate_sign_up_form(req)
        self.assertDictEqual({}, data)
        self.assertDictEqual(errors, {
            "first_name_error": "This must be completed",
            "surname_error": "This must be completed",
            "cellphone_error": "This must be completed",
            "terms_errors": "You must accept the terms and conditions to continue."
        })

        # Test correct data
        req = {"first_name": "Blarg", "surname": "Honk", "cellphone": "0123456789", 'terms': True}
        data, errors = validate_sign_up_form(req)
        self.assertDictEqual(req, data)
        self.assertDictEqual(errors, {})

        # Test invalid mobile
        req["cellphone"] = "blargblarg"
        data, errors = validate_sign_up_form(req)
        self.assertDictEqual(errors, {"cellphone_error": "Enter a valid cellphone number"})

    def test_validate_sign_up_form_normal(self):
        # Test no data
        req = {}
        data, errors = validate_sign_up_form_normal(req)
        self.assertDictEqual({}, data)
        self.assertDictEqual(errors, {
            "province_error": "This must be completed",
            "school_dirty_error": "This must be completed",
            "grade_error": "This must be completed"
        })

        # Test invalid province
        req = {"province": "No man's land", "school_dirty": "Honk", "grade": "Grade Eleventy"}
        data, errors = validate_sign_up_form_normal(req)
        self.assertDictContainsSubset({"province_error": "Select your province"}, errors)

        # Test almost correct data (no course)
        req = {"province": PROVINCES[0], "school_dirty": "Honk", "grade": "Grade 11"}
        data, errors = validate_sign_up_form_normal(req)
        self.assertDictEqual(errors, {'grade_course_error': "No course is assigned to your grade"})

        # Test correct data (with course)
        create_course(name=settings.GRADE_11_COURSE_NAME)
        req = {"province": PROVINCES[0], "school_dirty": "Honk", "grade": "Grade 11"}
        data, errors = validate_sign_up_form_normal(req)
        self.assertDictContainsSubset(req, data)
        self.assertDictEqual(errors, {})

    def test_validate_sign_up_form_school_confirm(self):
        # Test no data
        req = {}
        data, errors = validate_sign_up_form_school_confirm(req)
        self.assertDictEqual({}, data)
        self.assertDictEqual(errors, {"school_error": "This must be completed"})

        # Test invalid school
        req = {"school": "9999"}
        data, errors = validate_sign_up_form_school_confirm(req)
        self.assertDictContainsSubset({"school_error": "No such school exists"}, errors)

        # Test correct data
        org = create_organisation(name="Umbrella Corporation")
        school = create_school(name="Sam's School", organisation=org)
        req = {"school": school.pk}
        data, errors = validate_sign_up_form_school_confirm(req)
        self.assertDictContainsSubset(req, data)
        self.assertDictEqual(errors, {})

    def test_validate_accept_terms_and_conditions(self):
        # Test unchecked terms
        req = {"terms": False}
        data, errors = validate_sign_up_form(req)
        self.assertDictContainsSubset({"terms_errors": "You must accept the terms and conditions to continue."}, errors)

        # Test correct data
        req = {"first_name": "Blarg", "surname": "Honk", "cellphone": "0123456789", "terms": "True"}
        data, errors = validate_sign_up_form(req)
        self.assertDictContainsSubset(req, data)
        self.assertDictEqual(errors, {})

    def test_validate_accept_terms_and_conditions_after_redirect(self):
        # Test unchecked terms
        req = {"terms": False}
        data, errors = validate_accept_terms_form(req)
        self.assertDictContainsSubset({"terms_errors": "You must accept the terms and conditions to continue."}, errors)

        # Test correct data
        req = {"terms": "True"}
        data, errors = validate_accept_terms_form(req)
        self.assertDictContainsSubset(req, data)
        self.assertDictEqual(errors, {})

    def test_user_redirect_because_of_accept_terms(self):
        # Expect to be redirected to auth.accept_terms.html
        self.learner.terms_accept = False
        self.learner.save()
        resp = self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}), follow=True)
        self.assertRedirects(resp, reverse('auth.accept_terms'))

        # Expect there to be no redirect and just go straight to /home
        self.learner.terms_accept = True
        self.learner.save()
        resp = self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}), follow=True)
        self.assertRedirects(resp, reverse('learn.home'))
