from django.template.base import Node
from django.conf import settings
from django import template
from organisation.models import Course

register = template.Library()


class ResultModelsNode(Node):
    """
        Returns a list of modules for the fake results model
    """
    def render(self, context):
        models = []
        courses = Course.objects.all()
        for course in courses:
            models.append({"name": course.name, "id": course.id})

        context["results"] = models
        return ''


def result_models(parser, token):
    return ResultModelsNode()

var = register.tag(result_models)
