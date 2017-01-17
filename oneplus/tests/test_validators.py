from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from core.common import PROVINCES
from core.models import Setting
from organisation.models import Course, Organisation, School
from oneplus.validators import validate_mobile, validate_sign_up_form, validate_sign_up_form_normal, \
    validate_sign_up_form_school_confirm


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


# @override_settings(GRADE_11_COURSE_NAME='Gr 11 Course')
class ValidatorTests(TestCase):
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
            "cellphone_error": "This must be completed"
        })

        # Test correct data
        req = {"first_name": "Blarg", "surname": "Honk", "cellphone": "0123456789"}
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
