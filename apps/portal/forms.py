from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class PortalLoginForm(forms.Form):
    username = forms.CharField(
        label='Identifiant',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]', 'placeholder': 'Identifiant'}),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]', 'placeholder': 'Mot de passe'}),
    )


class PortalActivationForm(forms.Form):
    username = forms.CharField(
        label='Identifiant',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]', 'placeholder': 'Choisissez un identifiant'}),
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]', 'placeholder': 'Mot de passe'}),
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]', 'placeholder': 'Confirmez le mot de passe'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Les mots de passe ne correspondent pas.')
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error('password1', e)
        return cleaned
