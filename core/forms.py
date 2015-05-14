from django import forms
from core.models import Participant
from auth.models import Learner


class ParticipantCreationForm(forms.ModelForm):
    class Meta:
        model = Participant

    def save(self, commit=True):
        participant = super(ParticipantCreationForm, self).save(commit=False)
        learner = self.cleaned_data.get("learner")
        active_participant = Participant.objects.filter(learner=learner, is_active=True)
        if active_participant.exists():
            raise forms.ValidationError("This learner is currently an active participant in %s class. Learner cannot "
                                        "be an active participant in multiple classes once."
                                        % active_participant.first().classs__name)
        else:
            if commit:
                participant.save()
            return participant