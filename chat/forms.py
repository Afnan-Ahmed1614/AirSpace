from django import forms
from django.contrib.auth.models import User
from .models import Profile

# This form handles the "Guest -> User" conversion
class ClaimIdentityForm(forms.ModelForm):
    username = forms.CharField(label="New Callsign", widget=forms.TextInput(attrs={'class': 'w-full p-2 bg-gray-800 border border-green-700 rounded text-white'}))
    password = forms.CharField(label="Set Password", widget=forms.PasswordInput(attrs={'class': 'w-full p-2 bg-gray-800 border border-green-700 rounded text-white'}))
    
    # Optional Profile Pic (Locked by View if XP < 50)
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'text-sm text-gray-400'}))

    class Meta:
        model = User
        fields = ['username', 'password']
        
class EditNameForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'w-full p-2 bg-gray-800 border border-green-700 rounded text-white'})
        }
        
class ChangePasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-green-500 focus:outline-none',
        'placeholder': 'New Password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-green-500 focus:outline-none',
        'placeholder': 'Confirm New Password'
    }))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data