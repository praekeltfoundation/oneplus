import six
from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend, ElasticsearchSearchEngine, \
    ElasticsearchSearchQuery
from haystack.inputs import Clean, Exact, PythonData, Raw


class FuzzyBackend(ElasticsearchSearchBackend):
    def build_search_kwargs(self, query_string, **kwargs):
        if type(query_string) == type(dict):
            search_kwargs = query_string
        else:
            search_kwargs = super(FuzzyBackend, self).build_search_kwargs(query_string, **kwargs)

        root_q = search_kwargs.get('query', None)
        if root_q:
            root_q['bool'] = root_q.pop('filtered')
            bool_obj = root_q['bool']
            if bool_obj:
                bool_obj['must'] = bool_obj.pop('query')

        return search_kwargs
    

class FuzzySearchQuery(ElasticsearchSearchQuery):
    def build_query_fragment(self, field, filter_type, value):
        from haystack import connections
        query_frag = ''

        if not hasattr(value, 'input_type_name'):
            # Handle when we've got a ``ValuesListQuerySet``...
            if hasattr(value, 'values_list'):
                value = list(value)

            if isinstance(value, six.string_types):
                # It's not an ``InputType``. Assume ``Clean``.
                value = Clean(value)
            else:
                value = PythonData(value)

        # Prepare the query using the InputType.
        prepared_value = value.prepare(self)

        if not isinstance(prepared_value, (set, list, tuple)):
            # Then convert whatever we get back to what pysolr wants if needed.
            prepared_value = self.backend._from_python(prepared_value)

        # 'content' is a special reserved word, much like 'pk' in
        # Django's ORM layer. It indicates 'no special field'.
        if field == 'content':
            index_fieldname = ''
        else:
            index_fieldname = u'%s:' % connections[self._using].get_unified_index().get_index_fieldname(field)

        filter_types = {
            'contains': u'%s',
            'startswith': u'%s*',
            'exact': u'%s',
            'gt': u'{%s TO *}',
            'gte': u'[%s TO *]',
            'lt': u'{* TO %s}',
            'lte': u'[* TO %s]',
            'fuzzy': u'%s~',
        }

        if value.post_process is False:
            query_frag = prepared_value
        else:
            if filter_type in ['contains', 'startswith', 'fuzzy']:
                if value.input_type_name == 'exact':
                    query_frag = prepared_value
                else:
                    # Iterate over terms & incorportate the converted form of each into the query.
                    terms = []

                    if isinstance(prepared_value, six.string_types):
                        for possible_value in prepared_value.split(' '):
                            terms.append(filter_types[filter_type] % self.backend._from_python(possible_value))
                    else:
                        terms.append(filter_types[filter_type] % self.backend._from_python(prepared_value))

                    if len(terms) == 1:
                        query_frag = terms[0]
                    else:
                        query_frag = u"(%s)" % " AND ".join(terms)
            elif filter_type == 'in':
                in_options = []

                for possible_value in prepared_value:
                    in_options.append(u'"%s"' % self.backend._from_python(possible_value))

                query_frag = u"(%s)" % " OR ".join(in_options)
            elif filter_type == 'range':
                start = self.backend._from_python(prepared_value[0])
                end = self.backend._from_python(prepared_value[1])
                query_frag = u'["%s" TO "%s"]' % (start, end)
            elif filter_type == 'exact':
                if value.input_type_name == 'exact':
                    query_frag = prepared_value
                else:
                    prepared_value = Exact(prepared_value).prepare(self)
                    query_frag = filter_types[filter_type] % prepared_value
            else:
                if value.input_type_name != 'exact':
                    prepared_value = Exact(prepared_value).prepare(self)

                query_frag = filter_types[filter_type] % prepared_value

        if len(query_frag) and not isinstance(value, Raw):
            if not query_frag.startswith('(') and not query_frag.endswith(')'):
                query_frag = "(%s)" % query_frag

        return u"%s%s" % (index_fieldname, query_frag)


class FuzzyEngine(ElasticsearchSearchEngine):
    backend = FuzzyBackend
    query = FuzzySearchQuery