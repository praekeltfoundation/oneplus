from django.test import TestCase
from datetime import datetime
from mock import patch
from oneplus.filters import sub_months, get_timeframe_range


class TestFilterHelpers(TestCase):
    def test_sub_months(self):
        t = datetime(2015, 6, 5)

        # subtract nothing
        te = datetime(2015, 6, 5).date()
        ta = sub_months(t, 0).date()
        self.assertEquals(te, ta)

        # same year
        te = datetime(2015, 5, 5).date()
        ta = sub_months(t, 1).date()
        self.assertEquals(te, ta)

        te = datetime(2015, 3, 5).date()
        ta = sub_months(t, 3).date()
        self.assertEquals(te, ta)

        # wrap 1 year
        te = datetime(2014, 8, 5).date()
        ta = sub_months(t, 10).date()
        self.assertEquals(te, ta)

        #wrap 1 year boundaries
        te = datetime(2014, 12, 5).date()
        ta = sub_months(t, 6).date()
        self.assertEquals(te, ta)

        te = datetime(2014, 1, 5).date()
        ta = sub_months(t, 17).date()
        self.assertEquals(te, ta)

        #wrap 2 year boundaries
        te = datetime(2013, 12, 5).date()
        ta = sub_months(t, 18).date()
        self.assertEquals(te, ta)

        te = datetime(2013, 1, 5).date()
        ta = sub_months(t, 29).date()
        self.assertEquals(te, ta)

    def make_start_date(self, sd):
        return sd.replace(hour=0, minute=0, second=0, microsecond=0)

    def make_end_date(self, ed):
        return ed.replace(hour=23, minute=59, second=59, microsecond=999999)

    @patch("oneplus.filters.get_today")
    def test_get_timeframe_range(self, mock_get_today):

            mock_get_today.return_value = datetime(2015, 6, 1)

            # this week
            sde = self.make_start_date(datetime(2015, 6, 1))
            ede = self.make_end_date(datetime(2015, 6, 7))
            sda, eda = get_timeframe_range("0")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # default for junk values
            sda, eda = get_timeframe_range("9")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # last week
            sde = self.make_start_date(datetime(2015, 5, 25))
            ede = self.make_end_date(datetime(2015, 5, 31))
            sda, eda = get_timeframe_range("1")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # this month
            sde = self.make_start_date(datetime(2015, 6, 1))
            ede = self.make_end_date(datetime(2015, 6, 30))
            sda, eda = get_timeframe_range("2")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # last month
            sde = self.make_start_date(datetime(2015, 5, 1))
            ede = self.make_end_date(datetime(2015, 5, 31))
            sda, eda = get_timeframe_range("3")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # last 3 months
            sde = self.make_start_date(datetime(2015, 4, 1))
            ede = self.make_end_date(datetime(2015, 6, 30))
            sda, eda = get_timeframe_range("4")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # last 6 months
            sde = self.make_start_date(datetime(2015, 1, 1))
            ede = self.make_end_date(datetime(2015, 6, 30))
            sda, eda = get_timeframe_range("5")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # this year
            sde = self.make_start_date(datetime(2015, 1, 1))
            ede = self.make_end_date(datetime(2015, 12, 31))
            sda, eda = get_timeframe_range("6")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)

            # last year
            sde = self.make_start_date(datetime(2014, 1, 1))
            ede = self.make_end_date(datetime(2014, 12, 31))
            sda, eda = get_timeframe_range("7")
            self.assertEquals(sde, sda)
            self.assertEquals(ede, eda)