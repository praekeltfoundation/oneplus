# -*- coding: utf-8 -*-
from django.test import TestCase
from haystack_custom import FuzzyBackend, FuzzyEngine, FuzzySearchNode, FuzzySearchQuery, FUZZY_VALID_FILTERS


class TestHaystack(TestCase):
    def test_haystack_barebones(self):
        self.assertGreater(len(FUZZY_VALID_FILTERS), 0)
