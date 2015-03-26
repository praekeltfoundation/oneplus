from django.contrib import admin
from .models import *


class GamificationPointBonusAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "image", "value"]})
    ]


class GamificationBadgeTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "image_", "order")
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "image", "order"]})
    ]


class GamificationScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "description", "module", "course", "point", "badge")
    list_filter = ("name", "course", "module")
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "event", "course", "module"]}),
        ("Rewards",
            {"fields": ["point", "badge"]})
    ]


# Gamification
admin.site.register(GamificationPointBonus, GamificationPointBonusAdmin)
admin.site.register(GamificationBadgeTemplate, GamificationBadgeTemplateAdmin)
admin.site.register(GamificationScenario, GamificationScenarioAdmin)
