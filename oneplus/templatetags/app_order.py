from django.template.base import Node
from django.conf import settings
from django import template

register = template.Library()


class AppOrderNode(Node):
    """
        Reorders the app_list and child model lists on the admin index page.
    """
    def render(self, context):
        if 'app_list' in context:
            app_list = list(context['app_list'])
            ordered = []
            # look at each app in the user order
            for app in settings.ADMIN_REORDER:
                app_name, app_models = app[0], app[1]
                # look at each app in the orig order
                for app_def in app_list:
                    if app_def['name'] == app_name:
                        model_list = list(app_def['models'])
                        mord = []
                        # look at models in user order
                        for model_name in app_models:
                            # look at models in orig order
                            for model_def in model_list:
                                if model_def['name'] == model_name:
                                    mord.append(model_def)
                                    model_list.remove(model_def)
                                    break
                        mord[len(mord):] = model_list
                        ordered.append({'app_url': app_def['app_url'], 'models': mord, 'name': app_def['name']})
                        app_list.remove(app_def)
                        break
            ordered[len(ordered):] = app_list
            context['app_list'] = ordered
        return ''


def app_order(parser, token):
    return AppOrderNode()

var = register.tag(app_order)