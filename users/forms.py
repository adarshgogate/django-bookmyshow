from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        # Change 'user' to 'username'
        fields = ['username', 'email'] 
        # Note: You don't need 'password' here; UserCreationForm adds it automatically

class UserUpdateForm(forms.ModelForm): # Capital 'M' in ModelForm
    email = forms.EmailField()
    class Meta:
        model = User
        # Change 'user' to 'username'
        fields = ['username', 'email']   

class ProfileUpdateForm(forms.ModelForm): # Capital 'M' in ModelForm
    class Meta:
        model = User
        fields = ['email'] # Password should be handled by PasswordChangeForm, not here