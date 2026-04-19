from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

from accounts.models import Profile, User


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")


class AdminUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active", "is_staff", "is_superuser")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "avatar", "phone", "city", "country", "timezone")

