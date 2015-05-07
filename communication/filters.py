from django.contrib import admin
from django.db import connection
from django.db.models import Min
from datetime import datetime
from .models import *
from auth.models import CustomUser
import operator


class ModerationContentFilter(admin.SimpleListFilter):
    title = 'Content'
    parameter_name = 'content'

    def lookups(self, request, model_admin):
        if connection.vendor == 'sqlite':
            data = Moderation.objects.values('description').\
                annotate(uni_description=Min('description')).\
                order_by('uni_description')
        else:
            data = Moderation.objects.values('description').\
                distinct('description').\
                order_by('description')

        if connection.vendor == 'sqlite':
            return [(c['uni_description'], c['uni_description']) for c in data]
        else:
            return [(c.description, c.description) for c in data]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(description=self.value())


class UserFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        result = set(CustomUser.objects.all())
        return [(c.id, c.get_display_name())
                for c in sorted(result, key=operator.methodcaller('get_display_name'))]


class ModerationUserFilter(UserFilter):
    title = 'User'
    parameter_name = 'user'

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(author=self.value())


class ModerationContentTypeFilter(admin.SimpleListFilter):
    title = 'Content Type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Blog comment'),
            ('2', 'Discussion comment'),
            ('3', 'Chatroom comment')
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(type=self.value())


class ModerationStateFilter(admin.SimpleListFilter):
    title = 'State'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Has reply'),
            ('2', 'Has no reply'),
            ('3', 'Is published'),
            ('4', 'Is unpublished'),
            ('5', 'Is unpublished by community'),
            ('6', 'Is unpublished by moderator')
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            if self.value() == '1':
                return queryset.filter(response__isnull=False)
            elif self.value() == '2':
                return queryset.filter(response__isnull=True)
            elif self.value() == '3':
                return queryset.filter(moderated=True)
            elif self.value() == '4':
                return queryset.filter(moderated=False, unmoderated_date__isnull=False)
            elif self.value() == '5':
                return queryset.filter(moderated=False, unmoderated_date__isnull=False, unmoderated_by__is_staff=False)
            elif self.value() == '6':
                return queryset.filter(moderated=False, unmoderated_date__isnull=False, unmoderated_by__is_staff=True)
            else:
                return queryset


class BannedUserFilter(UserFilter):
    title = 'Banned User'
    parameter_name = 'banu'

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(banned_user=self.value())


class BanningUserFilter(UserFilter):
    title = 'Banning User'
    parameter_name = 'busr'

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(banning_user=self.value())