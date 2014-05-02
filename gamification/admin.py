from django.contrib import admin
from models import *

class GamificationPointBonusAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "image", "value"]})
    ]


class GamificationBadgeTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "image"]})
    ]


#Gamification
admin.site.register(GamificationPointBonus, GamificationPointBonusAdmin)
admin.site.register(GamificationBadgeTemplate, GamificationBadgeTemplateAdmin)