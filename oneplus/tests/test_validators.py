from django.test import TestCase
from oneplus.validators import validate_mobile


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
