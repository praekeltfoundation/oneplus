from django import forms
from core.models import Participant
from auth.models import Learner


class ParticipantCreationForm(forms.ModelForm):
    class Meta:
        model = Participant

    def clean_learner(self):
        learner = self.cleaned_data.get("learner")
        active_participant = Participant.objects.filter(learner=learner, is_active=True)
        if active_participant.exists():
            raise forms.ValidationError("This learner is currently an active participant in %s class. Learner cannot "
                                        "be an active participant in multiple classes at once."
                                        % active_participant.first().classs.name)
        return learner