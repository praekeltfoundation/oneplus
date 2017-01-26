# -*- coding: utf-8 -*-
from django.test import TestCase
from tablib import Dataset
from organisation.models import Organisation, School
from organisation.resources import SchoolResource


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name,
        organisation=organisation,
        **kwargs)


class TestOrganisation(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.get(name='One Plus')
        self.school = create_school('One Plus School', self.organisation)

    def test_school_import_org_pk(self):
        old_count = School.objects.all().count()
        dataset = Dataset(headers=('id', 'name', 'organisation'))
        dataset.append((None, 'Nu School', self.organisation.pk))
        sres = SchoolResource()
        sres.import_data(dataset, raise_errors=True)
        self.assertEqual(School.objects.all().count(), old_count + 1)
        School.objects.get(name='Nu School')

    def test_school_import_org_name(self):
        old_count = School.objects.all().count()
        dataset = Dataset(headers=('id', 'name', 'organisation'))
        dataset.append((None, 'Nu School', self.organisation.name))
        sres = SchoolResource()
        sres.import_data(dataset, raise_errors=True)
        self.assertEqual(School.objects.all().count(), old_count + 1)
        School.objects.get(name='Nu School')

    def test_school_import_multi(self):
        dataset = Dataset(headers=('id', 'name', 'organisation'))
        map(dataset.append, (
            (None, 'Nu School 1', self.organisation.name),
            (None, 'Nu School 2', self.organisation.name),
            (None, 'Nu School 3', self.organisation.name)))
        old_count = School.objects.all().count()
        sres = SchoolResource()
        sres.import_data(dataset, raise_errors=True)
        self.assertEqual(School.objects.all().count(), old_count + 3)
        School.objects.get(name='Nu School 1')
        School.objects.get(name='Nu School 2')
        School.objects.get(name='Nu School 3')
