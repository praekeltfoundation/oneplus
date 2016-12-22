from haystack import indexes
from .models import School


class SchoolIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    name = indexes.CharField(model_attr='name')
    province = indexes.CharField(model_attr='province', null=True)

    def get_model(self):
        return School

    def index_queryset(self, using=None):
        return self.get_model().objects.all()