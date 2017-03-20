from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext, NestedObjects, quote
from django.contrib.auth import get_permission_codename
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import router
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from import_export.admin import DEFAULT_FORMATS
from import_export.forms import ExportForm


def get_exported_objects(objs, opts, user, admin_site, using):
    """
    Find all objects related to ``objs`` that should also be deleted. ``objs``
    must be a homogenous iterable of objects (e.g. a QuerySet).

    Returns a nested list of strings suitable for display in the
    template with the ``unordered_list`` filter.

    """
    collector = NestedObjects(using=using)
    collector.collect(objs)
    perms_needed = set()

    def format_callback(obj):
        has_admin = obj.__class__ in admin_site._registry
        opts = obj._meta

        if has_admin:
            admin_url = reverse('%s:%s_%s_change'
                                % (admin_site.name,
                                   opts.app_label,
                                   opts.model_name),
                                None, (quote(obj._get_pk_val()),))
            p = '%s.%s' % (opts.app_label,
                           get_permission_codename('delete', opts))
            # Display a link to the admin page.
            return format_html('{0}: <a href="{1}">{2}</a>',
                               capfirst(opts.verbose_name),
                               admin_url,
                               obj)
        else:
            # Don't display link to edit, because it either has no
            # admin or is edited inline.
            return '%s: %s' % (capfirst(opts.verbose_name),
                               force_text(obj))

    to_export = objs

    protected = None

    return to_export, perms_needed, protected


def export_selected(modeladmin, request, queryset):
    """
    Action which exports the selected objects.

    This action first displays a confirmation page which shows all the
    exportable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change list.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label
    formats = modeladmin.get_export_formats()
    form = ExportForm(formats, request.POST or None)

    using = router.db_for_write(modeladmin.model)

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    exportable_objects, perms_needed, protected = get_exported_objects(
        queryset, opts, request.user, modeladmin.admin_site, using)

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get('post'):
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n and form.is_valid():
            file_format = formats[
                int(form.cleaned_data['file_format'])
            ]()
            export_data = modeladmin.get_export_data(file_format, queryset)
            content_type = file_format.get_content_type()
            # Django 1.7 uses the content_type kwarg instead of mimetype
            try:
                response = HttpResponse(export_data, content_type=content_type)
            except TypeError:
                response = HttpResponse(export_data, mimetype=content_type)
            response['Content-Disposition'] = 'attachment; filename=%s' % (
                modeladmin.get_export_filename(file_format),
            )
            return response
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    if perms_needed or protected:
        title = _("Cannot export %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        "title": title,
        "objects_name": objects_name,
        "exportable_objects": [exportable_objects],
        "form": form,
        'queryset': queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return TemplateResponse(request, [
        "admin/%s/%s/export_selected_confirmation.html" % (app_label, opts.model_name),
        "admin/%s/export_selected_confirmation.html" % app_label,
        "admin/export_selected_confirmation.html"
    ], context, current_app=modeladmin.admin_site.name)
export_selected.short_description = ugettext_lazy("Export selected %(verbose_name_plural)s")
