from import_export import resources
from .models import Enterprise, Vehicle, Trip, TrackPoint, Driver
from geopy.exc import GeopyError
from geopy.geocoders import Yandex
from import_export import resources, fields
from import_export.widgets import ManyToManyWidget


class EnterpriseResource(resources.ModelResource):
    """
    Ресурс для импорта/экспорта моделей Enterprise
    """
    class Meta:
        model = Enterprise
        # Поля, которые будут участвовать в импорте/экспорте
        fields = (
            'id',
            'name',
            'city',
            'timezone',
        )
        export_order = fields  # порядок столбцов при экспорте


class VehicleResource(resources.ModelResource):
    """
    Ресурс для импорта/экспорта автомобилей.
    По умолчанию поля ForeignKey (model, documentation, enterprise, active_driver) 
    будут представлены их ID.
    Если нужно подгружать/импортировать строки (например, название модели), 
    используйте ForeignKeyWidget.
    """
    drivers_list = fields.Field(
        column_name='drivers',
        attribute='drivers',  # ссылка на ManyToMany
        widget=ManyToManyWidget(Driver, field='id')
        # здесь указываем, что храним список driver.id через запятую
    )

    class Meta:
        model = Vehicle
        fields = (
            'id',
            'cost',
            'year_of_production',
            'mileage',
            'color',
            'transmission',
            'fuel_type',
            'model',
            'documentation',
            'enterprise',
            'purchase_date',
            'drivers_list',
            'active_driver',
        )
        export_order = fields

def get_address_for_point(point):
    """
    Получить адрес через Яндекс Геокодер (geopy).
    point.x - долгота, point.y - широта
    """
    api_key = '38974648-aae9-4e6f-bdfb-9a64a05c5c91'

    # Создаём объект для геокодирования
    geolocator = Yandex(
        api_key=api_key,
        user_agent="cars",  # Можно указать любое название
        timeout=5,            # Таймаут для HTTP-запроса
    )

    try:
        # Для обратного геокодирования geopy ожидает координаты в формате (широта, долгота)
        location = geolocator.reverse((point.y, point.x))

        if location and location.address:
            return location.address
        else:
            return "Адрес не найден"
    except GeopyError as e:
        return f"Ошибка при обращении к Яндекс Геокодеру: {str(e)}"
        
class TripResource(resources.ModelResource):
    start_address = fields.Field()  # виртуальное поле
    end_address = fields.Field()

    class Meta:
        model = Trip
        fields = ('id', 'vehicle', 'start_time', 'end_time', 'duration',
                  'start_address', 'end_address')

    def dehydrate_start_address(self, trip):
        # находим первую точку за время trip.start_time
        track_point = trip.vehicle.track_points.filter(
            timestamp__gte=trip.start_time,
            timestamp__lte=trip.end_time
        ).order_by('timestamp').first()
        if track_point:
            return get_address_for_point(track_point.location)
        return ""

    def dehydrate_end_address(self, trip):
        track_point = trip.vehicle.track_points.filter(
            timestamp__gte=trip.start_time,
            timestamp__lte=trip.end_time
        ).order_by('timestamp').last()
        if track_point:
            return get_address_for_point(track_point.location)
        return ""
        
class TrackPointResource(resources.ModelResource):
    lat = fields.Field()
    lon = fields.Field()

    class Meta:
        model = TrackPoint
        fields = ('id', 'vehicle', 'timestamp')  # без location, мы сами обработаем

    def dehydrate_lat(self, obj):
        # lat = y
        return obj.location.y if obj.location else None

    def dehydrate_lon(self, obj):
        # lon = x
        return obj.location.x if obj.location else None

    def before_save_instance(self, instance, using_transactions, dry_run):
        # При импорте смотрим, есть ли lat/lon в row
        # (Нужно либо before_import_row, либо widget на lat/lon)
        row = self.current_row  # строка CSV
        lat_val = row.get('lat')
        lon_val = row.get('lon')
        if lat_val and lon_val and not dry_run:
            lat = float(lat_val)
            lon = float(lon_val)
            instance.location = Point(lon, lat)
        return super().before_save_instance(instance, using_transactions, dry_run)



