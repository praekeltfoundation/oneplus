from django import forms
from communication.models import Message
from auth.models import CustomUser


class MessageForm(forms.ModelForm):

    users = forms.ModelChoiceField(queryset=CustomUser.objects.all(), label="")

    def save(self, commit=True):
        extra_field = self.cleaned_data.get('users', None)
        # ...do something with extra_field here...
        return super(MessageForm, self).save(commit=commit)

    class Meta:
        model = Message