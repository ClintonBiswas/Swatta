from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

User = get_user_model()  # Get the custom user model

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        """ Validate if the email exists in the database. """
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is not registered with us.")
        return email

