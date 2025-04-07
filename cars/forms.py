from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Vehicle, Driver, Enterprise


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
        
       
class ReportForm(forms.Form):
    REPORT_TYPES = (
        ('car_mileage', 'Пробег автомобиля'),
        ('driver_time', 'Время езды водителя'),
        ('enterprise_active_cars', 'Пробег активных автомобилей предприятия'),
    )

    report_type = forms.ChoiceField(choices=REPORT_TYPES, label="Тип отчёта")
    period = forms.ChoiceField(choices=(('day', 'День'), ('month', 'Месяц'), ('year', 'Год')), initial='day', label="Период")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Дата начала")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Дата конца")

    # Поля, которые будут динамически отображаться
    vehicle = forms.ModelChoiceField(queryset=Vehicle.objects.all(), required=False, label="Транспортное средство")
    driver = forms.ModelChoiceField(queryset=Driver.objects.all(), required=False, label="Водитель")
    enterprise = forms.ModelChoiceField(queryset=Enterprise.objects.all(), required=False, label="Предприятие")

    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')

        if report_type == 'car_mileage' and not cleaned_data.get('vehicle'):
            self.add_error('vehicle', 'Это поле обязательно для выбранного типа отчёта.')

        if report_type == 'driver_time' and not cleaned_data.get('driver'):
            self.add_error('driver', 'Это поле обязательно для выбранного типа отчёта.')

        if report_type == 'enterprise_active_cars' and not cleaned_data.get('enterprise'):
            self.add_error('enterprise', 'Это поле обязательно для выбранного типа отчёта.')
            
class TripUploadForm(forms.Form):
    # Форма для загрузки поездки
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Начало поездки"
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Окончание поездки"
    )
    gpx_file = forms.FileField(label="GPX файл")

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("Время начала должно быть раньше времени окончания.")
        return cleaned_data

