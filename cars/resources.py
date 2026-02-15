from import_export import resources
from .models import Enterprise, Vehicle, Trip, TrackPoint, Driver
from import_export import resources, fields
from import_export.widgets import ManyToManyWidget
from django.contrib.gis.geos import Point
from .utils import get_address_for_point



class EnterpriseResource(resources.ModelResource):
    """
    Ресурс для импорта/экспорта моделей Enterprise
    """
    class Meta:
        model = Enterprise
        fields = (
            'id',
            'name',
            'city',
            'timezone',
        )
        export_order = fields


class VehicleResource(resources.ModelResource):
    """
    Ресурс для импорта/экспорта автомобилей.
    """
    drivers_list = fields.Field(
        column_name='drivers',
        attribute='drivers',
        widget=ManyToManyWidget(Driver, field='id')
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
        
class TripResource(resources.ModelResource):
    start_address = fields.Field()
    end_address = fields.Field()

    class Meta:
        model = Trip
        fields = ('id', 'vehicle', 'start_time', 'end_time', 'duration',
                  'start_address', 'end_address')

    def dehydrate_start_address(self, trip):
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
        fields = ('id', 'vehicle', 'timestamp')

    def dehydrate_lat(self, obj):
        # lat = y
        return obj.location.y if obj.location else None

    def dehydrate_lon(self, obj):
        # lon = x
        return obj.location.x if obj.location else None

    def before_save_instance(self, instance, using_transactions, dry_run):
        row = self.current_row  # строка CSV
        lat_val = row.get('lat')
        lon_val = row.get('lon')
        if lat_val and lon_val and not dry_run:
            lat = float(lat_val)
            lon = float(lon_val)
            instance.location = Point(lon, lat)
        return super().before_save_instance(instance, using_transactions, dry_run)



