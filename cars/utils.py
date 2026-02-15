from django.utils.timezone import localtime
import zoneinfo
from geopy.exc import GeopyError
from geopy.geocoders import Yandex
import datetime
from django.db.models import Sum
from .models import Vehicle, Trip, CarMileageReport, TrackPoint, DriverTimeReport, Driver, EnterpriseActiveCarsReport, Enterprise

def convert_to_enterprise_timezone(vehicle):
    tz = zoneinfo.ZoneInfo(vehicle.enterprise.timezone)
    return localtime(vehicle.purchase_date, tz)
    
    
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
        

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance (km) between two points on the Earth
    specified by latitude/longitude.
    """
    R = 6371  # Earth radius in kilometers
    from math import radians, sin, cos, sqrt, atan2

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def generate_car_mileage_report(vehicle_id, start_date, end_date, period):
    """
    Генерирует отчет о пробеге одного авто за период.
    Возвращает объект CarMileageReport.
    """
    vehicle = Vehicle.objects.get(pk=vehicle_id)

    trips = Trip.objects.filter(
        vehicle=vehicle,
        start_time__date__gte=start_date,
        end_time__date__lte=end_date
    ).order_by('start_time')

    def calculate_trip_distance(trip):
        points = TrackPoint.objects.filter(
            vehicle=vehicle,
            timestamp__gte=trip.start_time,
            timestamp__lte=trip.end_time
        ).order_by('timestamp')

        distance_sum = 0.0
        prev_point = None

        for tp in points:
            if prev_point:
                lon1, lat1 = prev_point.location.x, prev_point.location.y
                lon2, lat2 = tp.location.x, tp.location.y
                distance_sum += haversine_distance(lat1, lon1, lat2, lon2)
            prev_point = tp

        return distance_sum

    grouped_data = {}
    for trip in trips:
        dist = calculate_trip_distance(trip)

        if period == 'day':
            key = trip.start_time.strftime('%Y-%m-%d')
        elif period == 'month':
            key = trip.start_time.strftime('%Y-%m')
        elif period == 'year':
            key = trip.start_time.strftime('%Y')
        else:
            key = trip.start_time.strftime('%Y-%m-%d')

        grouped_data[key] = grouped_data.get(key, 0) + dist

    data_list = []
    for time_key in sorted(grouped_data.keys()):
        data_list.append({"time": time_key, "value": round(grouped_data[time_key], 3)})

    result_json = {
        "data": data_list,
        "unit": "km"
    }

    report = CarMileageReport.objects.create(
        name="Пробег ТС за период",
        start_date=start_date,
        end_date=end_date,
        period=period,
        vehicle=vehicle,
        result=result_json
    )
    return report
    

def generate_driver_time_report(driver_id, start_date, end_date, period):
    """
    Суммарная длительность (часов) поездок данного водителя за период,
    сгруппированная по day/month/year.
    """
    driver = Driver.objects.get(pk=driver_id)

    # Предположим, что Trip имеет поле driver=ForeignKey(Driver).
    # Если у вас другая логика, подправьте.
    trips = Trip.objects.filter(
        vehicle__active_driver=driver,
        start_time__date__gte=start_date,
        end_time__date__lte=end_date
    ).order_by('start_time')

    grouped_data = {}
    for trip in trips:
        # trip.duration – timedelta
        hours = trip.duration.total_seconds() / 3600.0 if trip.duration else 0.0

        if period == 'day':
            key = trip.start_time.strftime('%Y-%m-%d')
        elif period == 'month':
            key = trip.start_time.strftime('%Y-%m')
        elif period == 'year':
            key = trip.start_time.strftime('%Y')
        else:
            key = trip.start_time.strftime('%Y-%m-%d')

        grouped_data[key] = grouped_data.get(key, 0) + hours

    data_list = []
    for time_key in sorted(grouped_data.keys()):
        data_list.append({"time": time_key, "hours": round(grouped_data[time_key], 2)})

    result_json = {
        "data": data_list,
        "unit": "hours"
    }

    report = DriverTimeReport.objects.create(
        name="Время езды водителя",
        start_date=start_date,
        end_date=end_date,
        period=period,
        driver=driver,
        result=result_json
    )
    return report
    
    
def generate_enterprise_active_cars_report(enterprise_id, start_date, end_date, period):
    """
    Для заданного enterprise находим все авто, у которых active_driver != None.
    Для каждого авто считаем пробег (через TrackPoint/Trip) с учётом period.

    В итоге report.result = {
      "cars": [
        {
          "car_id": 123,
          "driver_name": "Иван Иванов",
          "mileage_data": [
            {"time": "2025-01-01", "value": 120.5},
            {"time": "2025-01-02", "value": 80.1},
            ...
          ]
        },
        ...
      ]
    }
    """
    enterprise = Enterprise.objects.get(pk=enterprise_id)

    # 1) Ищем все авто, где active_driver != None
    vehicles = Vehicle.objects.filter(
        enterprise=enterprise,
        active_driver__isnull=False
    )

    cars_result = []

    for vehicle in vehicles:
        driver = vehicle.active_driver
        driver_name = driver.name if driver else None

        # Логика "пробег" (как в generate_car_mileage_report):

        # Находим поездки:
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__date__gte=start_date,
            end_time__date__lte=end_date
        ).order_by('start_time')

        def calculate_trip_distance(trip):
            points = TrackPoint.objects.filter(
                vehicle=vehicle,
                timestamp__gte=trip.start_time,
                timestamp__lte=trip.end_time
            ).order_by('timestamp')

            distance_sum = 0.0
            prev = None
            for tp in points:
                if prev:
                    lon1, lat1 = prev.location.x, prev.location.y
                    lon2, lat2 = tp.location.x, tp.location.y
                    distance_sum += haversine_distance(lat1, lon1, lat2, lon2)
                prev = tp
            return distance_sum

        grouped_data = {}
        for trip in trips:
            dist = calculate_trip_distance(trip)
            if period == 'day':
                key = trip.start_time.strftime('%Y-%m-%d')
            elif period == 'month':
                key = trip.start_time.strftime('%Y-%m')
            elif period == 'year':
                key = trip.start_time.strftime('%Y')
            else:
                key = trip.start_time.strftime('%Y-%m-%d')

            grouped_data[key] = grouped_data.get(key, 0.0) + dist

        mileage_data = []
        for tkey in sorted(grouped_data.keys()):
            mileage_data.append({
                "time": tkey,
                "value": round(grouped_data[tkey], 3)
            })

        # Сохраняем результат для этого авто
        if mileage_data:
            cars_result.append({
                "car_id": vehicle.id,
                "driver_name": driver_name,
                "mileage_data": mileage_data
            })

    # 2) Собираем final JSON:
    final_result = {
        "cars": cars_result,
        "info": {
            "enterprise_id": enterprise_id,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "period": period
        }
    }

    # 3) Создаём запись EnterpriseActiveCarsReport
    report = EnterpriseActiveCarsReport.objects.create(
        name="Активные авто + пробег",
        start_date=start_date,
        end_date=end_date,
        period=period,
        enterprise=enterprise,
        result=final_result
    )
    return report
