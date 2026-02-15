from time import localtime
from zoneinfo import ZoneInfo
from rest_framework import serializers
from .models import Vehicle, Enterprise, Driver, TrackPoint


class VehicleSerializer(serializers.ModelSerializer):
    local_purchase_date = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [ 
            'id',
            'local_purchase_date',
            'cost',
            'year_of_production',
            'mileage',
            'color',
            'transmission',
            'fuel_type',
            'active_driver',
            'model',
            'documentation',
            'enterprise',
            'drivers',
        ]

    def get_local_purchase_date(self, obj):
        try:
            enterprise_tz = ZoneInfo(obj.enterprise.timezone) if obj.enterprise and obj.enterprise.timezone else ZoneInfo("UTC")
        except Exception:
            enterprise_tz = ZoneInfo("UTC")

        if obj.purchase_date:
            try:
                purchase_date_local = obj.purchase_date.astimezone(enterprise_tz)
                return purchase_date_local.strftime('%d.%m.%Y %H:%M:%S')
            except Exception as e:
                print(f"Error converting time for vehicle {obj.id}: {e}")
                return None
        return None




class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'
        
class AuthTokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    
class CustomAuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class TrackPointSerializer(serializers.ModelSerializer):
    local_date = serializers.SerializerMethodField()
    
    class Meta:
        model = TrackPoint
        fields = ['local_date', 'location']

    def get_local_date(self, obj):
        # Преобразуем время точки в локальное для удобства
        enterprise = obj.vehicle.enterprise  # Получаем предприятие через связь
        local_time = enterprise.to_local_time(obj.timestamp)
        return local_time.isoformat()

class TrackPointRequestSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    output_format = serializers.ChoiceField(choices=["json", "geojson"])

class TripAPIRequestSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

class TripSummaryRequestSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
