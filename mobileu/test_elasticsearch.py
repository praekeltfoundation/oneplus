# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings

from organisation.models import Organisation, School
from .mobileu_elasticsearch import SchoolIndex


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name,
        organisation=organisation,
        **kwargs)


@override_settings(ELASTICSEARCH_INDEX_PREFIX='test_oneplus')
class TestSchoolIndex(TestCase):
    def setUp(self):
        try:
            self.school_index = SchoolIndex()
            self.school_index.ensure_index()
        except Exception as e:
            self.skipTest('ElasticSearch not available.')

    def tearDown(self):
        self.school_index.delete_index()
