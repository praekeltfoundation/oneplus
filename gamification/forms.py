from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import GamificationScenario
from django import forms


class GamificationScenarioForm(forms.ModelForm):

    def clean_point(self):
        p = self.cleaned_data.get('point', None)
        if not p:
            raise ValidationError('A Scenario needs to be associated with a Point')
        return p

    class Meta:
        model=GamificationScenario