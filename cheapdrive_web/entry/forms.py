from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail


User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    """
    Form for registering a new user with password confirmation.
    
    The form includes fields for the user's username, email, and password. 
    It also includes a second password field to confirm that both passwords match. 
    When the form is valid, it hashes the password and saves the user to the database.
    """

    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email")
        help_texts = {"username": None, "email": None}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
