from django import forms
from communication.models import Message


class MessageCreationForm(forms.ModelForm):

    users = forms.MultipleChoiceField(choices='', label="")

    def save(self, commit=True):
        message = super(MessageCreationForm, self).save(commit=False)
        message.name = self.cleaned_data["users"]
        if commit:
            message.save()
        return message

    class Meta:
        model = Message
