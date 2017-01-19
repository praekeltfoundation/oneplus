from django import forms
from django.core.validators import ValidationError
from validators import validate_mobile


def validate_username(username):
        if not validate_mobile(username):
            raise ValidationError('Please enter a valid cellphone number.')


class LoginForm(forms.Form):
    username = forms.CharField(label="Phone Number", validators=[validate_username])
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )


class SmsPasswordForm(forms.Form):
    msisdn = forms.CharField(label="Phone Number")


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput
    )

    password_2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )
