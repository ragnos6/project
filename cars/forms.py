from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Vehicle


class ManagerLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )
    
class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['cost', 'year_of_production', 'mileage', 'color', 'transmission', 'fuel_type', 'model']
        widgets = {
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'year_of_production': forms.NumberInput(attrs={'class': 'form-control'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'transmission': forms.Select(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-control'}),
            'model': forms.Select(attrs={'class': 'form-control'}),
        }
