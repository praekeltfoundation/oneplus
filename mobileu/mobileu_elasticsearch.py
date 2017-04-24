from django.utils.timezone import now
from django.conf import settings
from elasticsearch import helpers as es_help, Elasticsearch
from organisation.models import School

school_index_name = 'oneplus_schools'

es = Elasticsearch([settings.ELASTICSEARCH_URL])


def ensure_indices():
    if not es.indices.exists(school_index_name):
        es.indices.create(school_index_name)


def update_school_index(update_time=now(), delete_stale=False):
    update_gen = ({
            '_id': school.pk,
            '_index': school_index_name,
            '_op_type': 'index',
            'date_updated': update_time,
            'name': school.name,
            'province': school.province,
        } for school in School.objects.all())

    num_successful, errors = es_help.bulk(es, update_gen)

    if errors:
        pass

    if delete_stale:
        es.delete_by_query(school_index_name, {'range': {'date_updated': {'lt': update_time}}})
