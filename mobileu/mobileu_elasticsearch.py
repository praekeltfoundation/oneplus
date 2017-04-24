from django.utils.timezone import now
from django.conf import settings
from elasticsearch import helpers as es_help, Elasticsearch
from organisation.models import School


es = Elasticsearch([settings.ELASTICSEARCH_URL])


def ensure_indices():
    school_idx = SchoolIndex()
    if not es.indices.exists(school_idx.index_name):
        es.indices.create(school_idx.index_name)


class ElasticSearchIndex:
    base_index_name = None
    index_name = None

    def __init__(self):
        if settings.ELASTICSEARCH_INDEX_PREFIX:
            self.index_name = settings.ELASTICSEARCH_INDEX_PREFIX + self.base_index_name
        else:
            self.index_name = self.base_index_name

    def ensure_index(self):
        if not self.index_name:
            raise AssertionError('Index name not set.')

        if not es.indices.exists(self.index_name):
            es.indices.create(self.index_name)

    def delete_index(self):
        if not self.index_name:
            raise AssertionError('Index name not set.')

        es.indices.delete(self.index_name)


class SchoolIndex(ElasticSearchIndex):
    base_index_name = 'school'

    def update_index(self, update_time=now(), delete_stale=False):
        update_gen = ({
                '_id': school.pk,
                '_index': self.index_name,
                '_op_type': 'index',
                'date_updated': update_time,
                'name': school.name,
                'province': school.province,
            } for school in School.objects.all())

        num_successful, errors = es_help.bulk(es, update_gen)

        if errors:
            pass

        if delete_stale:
            es.delete_by_query(self.index_name, {'range': {'date_updated': {'lt': update_time}}})

        return num_successful, errors
