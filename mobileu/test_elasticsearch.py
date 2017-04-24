# -*- coding: utf-8 -*-
from time import sleep
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


@override_settings(ELASTICSEARCH_INDEX_PREFIX='test_oneplus_')
class TestSchoolIndex(TestCase):
    def setUp(self):
        try:
            self.school_index = SchoolIndex()
            self.school_index.ensure_index()
        except Exception as e:
            self.skipTest('ElasticSearch not available.')
            return

        self.organisation = create_organisation('Test Org')

    def tearDown(self):
        self.school_index.delete_index()

    def test_update(self):
        num_schools = 10
        for i in xrange(num_schools):
            create_school('School %i' % (i,), self.organisation, province='Gauteng')

        self.school_index.update_index()
        sleep(1)
        self.assertEqual(self.school_index.count(), School.objects.count())

    def test_rebuild(self):
        num_schools = 10
        for i in xrange(num_schools):
            create_school('School %i' % (i,), self.organisation, province='Gauteng')

        self.school_index.rebuild_index()
        sleep(1)
        self.assertEqual(self.school_index.count(), School.objects.count())
        self.school_index.rebuild_index()
        sleep(1)
        self.assertEqual(self.school_index.count(), School.objects.count())

    def test_search(self):
        num_schools = 10
        for i in xrange(num_schools):
            create_school('School %i' % (i + 1,), self.organisation, province='Gauteng')
        create_school('FREEDOM', self.organisation, province='Western Cape')
        self.school_index.update_index()
        sleep(1)

        # test constrained name and province
        results = self.school_index.search_name(search='School 1', province='Gauteng')
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['_source']['name'], 'School 1')

        results = self.school_index.search_name(search='freedome', province='Western Cape')
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['_source']['name'], 'FREEDOM')

        # test constrained name
        results = self.school_index.search_name(search='School 1')
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['_source']['name'], 'School 1')

        results = self.school_index.search_name(search='School 1')
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['_source']['name'], 'School 1')

        # test constrained province
        results = self.school_index.search_name(province='Western Cape')
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['_source']['name'], 'FREEDOM')

