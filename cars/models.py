from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from zoneinfo import available_timezones, ZoneInfo
from django.utils.timezone import now, get_default_timezone_name, localtime
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.indexes import GistIndex
from django.contrib.postgres.fields import JSONField


# Модель документации
class VehicleDocumentation(models.Model):
    vin_number = models.CharField("VIN-код", max_length=17, unique=True)
    pts_number = models.CharField("Паспорт ТС (ПТС)", max_length=15, unique=True)
    reg_number = models.CharField("Номер автомобиля", max_length=10, unique=True)
    registration_date = models.DateField("Дата регистрации") 
    owner_name = models.CharField("ФИО владельца", max_length=100) 

    def __str__(self):
        return f'Документация {self.vin_number}'

    class Meta:
        verbose_name = "Документация автомобиля"
        verbose_name_plural = "Документация автомобилей"
     
        
# Модель организации
class Enterprise(models.Model):
    name = models.CharField('Название', max_length=50)
    city = models.CharField('Город', max_length=50)
    timezone = models.CharField(
        'Часовой пояс',
        max_length=50,
        choices=[(tz, tz) for tz in available_timezones()],
        default=get_default_timezone_name
    )

    def __str__(self):
        return f"{self.name} ({self.city})"

    def attached_vehicles(self):
        return self.vehicles.all()

    def to_local_time(self, utc_datetime):
        local_tz = ZoneInfo(self.timezone)
        return utc_datetime.astimezone(local_tz)
        
    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
     
     
# Модель менеджера
class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Менеджер (пользователь)')
    enterprises = models.ManyToManyField(Enterprise, related_name='managers', verbose_name='Предприятия')
    
    def __str__(self):
        return f"Менеджер: {self.user.username}"
        
    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"
        
        
# Модель водителя
class Driver(models.Model):
    name = models.CharField('ФИО', max_length=50)
    age = models.PositiveIntegerField("Возраст")
    salary = models.PositiveIntegerField("Зарплата")
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.SET_NULL,
        verbose_name="Предприятие",
        null =True,
        blank=True,
        default=4
    )
      
    def clean(self):
        if self.pk:  # Если объект уже существует
            original = Driver.objects.get(pk=self.pk)
            if original.enterprise != self.enterprise:
                # Проверяем, активен ли водитель на каком-то автомобиле
                if Vehicle.objects.filter(active_driver=self).exists():
                    raise ValidationError(
                        "Нельзя сменить предприятие водителя, пока он активен на автомобиле."
                    )
                                        
    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"  


# Модель модели авто
class Model(models.Model):
    name = models.CharField("Модель", max_length=50, unique=True)
    vehicle_type = models.CharField("Тип транспорта", max_length=20, choices=[
        ('passenger', 'Легковой'),
        ('truck', 'Грузовой'),
        ('bus', 'Автобус'),
        ('unmanned', 'Беспилотный'),
        ('motorcycle', 'Мотоцикл')
    ])
    power_capacity = models.PositiveIntegerField("Мощность автомобиля")
    fuel_capacity = models.PositiveIntegerField("Ёмкость бака (л)")
    payload_capacity = models.PositiveIntegerField("Грузоподъёмность (кг)", null=True, blank=True)
    seating_capacity = models.PositiveIntegerField("Количество мест")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Модель"
        verbose_name_plural = "Модели"


# Модель авто
class Vehicle(models.Model):
    cost = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    year_of_production = models.PositiveIntegerField('Год выпуска')
    mileage = models.PositiveIntegerField('Пробег (км)')
    color = models.CharField('Цвет', max_length=30)
    transmission = models.CharField("Коробка передач", max_length=20, choices=[
        ('manual', 'Механическая'),
        ('automatic', 'Автоматическая')
    ])
    
    active_driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Активный водитель',
        related_name='active_vehicles',
        default=None
    )
        
    fuel_type = models.CharField("Тип топлива", max_length=20, choices=[
        ('gasoline', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Электро'),
        ('hybrid', 'Гибрид')
    ])
    
    model = models.ForeignKey(
        Model, 
        on_delete=models.CASCADE, 
        related_name="vehicles", 
        verbose_name="Модель автомобиля",
        null =True,
        blank=False,
        default=5,
    )
    
    documentation = models.OneToOneField(
        VehicleDocumentation, 
        on_delete=models.CASCADE, 
        verbose_name="Документация", 
        null =True,
        blank=True,
    )
    
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.SET_NULL,
        related_name="vehicles",
        verbose_name="Предприятие",
        null =True,
        blank=True,
        default=4
    )
    drivers = models.ManyToManyField(
        Driver,
        through='VehicleDriver',
        related_name='vehicles',
    )
    purchase_date = models.DateTimeField(
        verbose_name="Дата и время покупки",
        default=now
    )

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-year_of_production']

    @property
    def local_purchase_date(self):
        if self.enterprise and self.enterprise.timezone:
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(self.enterprise.timezone)
                return localtime(self.purchase_date, tz)
            except Exception:
                pass
        # Если что-то пошло не так, возвращаем время в UTC
        return localtime(self.purchase_date)

    def clean(self):
        if self.active_driver and self.active_driver not in self.drivers.all():
            raise ValidationError("Активный водитель должен быть среди назначенных на автомобиль.")
        if self.pk:  # Если объект уже существует
            original = Vehicle.objects.get(pk=self.pk)
            if original.enterprise != self.enterprise:
                # Проверяем, есть ли у автомобиля активный водитель
                if self.active_driver is not None:
                    raise ValidationError(
                        "Нельзя сменить предприятие автомобиля, пока у него есть активный водитель."
                    )
    def __str__(self):
        return f'{self.model}, цвет {self.color}, год выпуска - {self.year_of_production}'

        
class VehicleDriver(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="Водитель")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vehicle', 'driver'], name='unique_vehicle_driver')
        ]

    def __str__(self):
        return f"{self.driver.name} - {self.vehicle.model.name}"
        
class TrackPoint(models.Model):
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='track_points')
    timestamp = models.DateTimeField(default=now)
    location = gis_models.PointField()
    
class Trip(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField(null=True, blank=True)  # Поле для хранения интервала

    def save(self, *args, **kwargs):
        # Вычисление интервала между start_time и end_time перед сохранением
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trip for {self.vehicle} from {self.start_time} to {self.end_time}"

class Report(models.Model):
    """
    Базовая модель отчёта.
    """
    name = models.CharField("Название отчета", max_length=200)
    start_date = models.DateField("Начальная дата")
    end_date = models.DateField("Конечная дата")

    PERIODS = [
        ('day', 'Сутки'),
        ('month', 'Месяц'),
        ('year', 'Год'),
    ]
    period = models.CharField(
        choices=PERIODS, 
        max_length=5, 
        default='day', 
        verbose_name='Отчетный период'
    )

    result = models.JSONField("Результат", null=True, blank=True)
    report_type = models.CharField(
        "Тип отчёта", 
        max_length=100, 
        default="BaseReport"
    )

    created_at = models.DateTimeField("Дата создания", auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} [{self.report_type}] ({self.start_date} — {self.end_date})"

    class Meta:
        verbose_name = "Отчёт"
        verbose_name_plural = "Отчёты"


class CarMileageReport(Report):
    """
    Отчёт по пробегу одного автомобиля за период.
    """
    vehicle = models.ForeignKey(
        'Vehicle', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = "Отчёт: Пробег ТС"
        verbose_name_plural = "Отчёты: Пробег ТС"

    def save(self, *args, **kwargs):
        if not self.report_type:
            self.report_type = "CarMileageReport"
        super().save(*args, **kwargs)


class DriverTimeReport(Report):
    """
    Отчёт по времени езды водителя за период.
    """
    driver = models.ForeignKey(
        'Driver',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Отчёт: Время езды водителя"
        verbose_name_plural = "Отчёты: Время езды водителей"

    def save(self, *args, **kwargs):
        if not self.report_type:
            self.report_type = "DriverTimeReport"
        super().save(*args, **kwargs)


class EnterpriseActiveCarsReport(Report):
    """
    Отчёт по автомобилям предприятия с активными водителями за период.
    """
    enterprise = models.ForeignKey(
        'Enterprise',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Отчёт: Активные авто предприятия"
        verbose_name_plural = "Отчёты: Активные авто предприятий"

    def save(self, *args, **kwargs):
        if not self.report_type:
            self.report_type = "EnterpriseActiveCarsReport"
        super().save(*args, **kwargs)

