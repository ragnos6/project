from typing import List
from zoneinfo import ZoneInfo
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

from django.utils.dateparse import parse_datetime

from .models import Vehicle, Enterprise, Trip, TrackPoint, Driver
from .utils import generate_car_mileage_report, generate_driver_time_report, generate_enterprise_active_cars_report, \
    get_address_for_point
from .dto import TrackPointRequestDTO, TrackPointResponseDTO, TripSummaryRequestDTO, TripSummaryDTO, VehicleDetailDTO, \
    ReportRequestDTO, TripUploadDTO
import gpxpy
import json


class TrackService:
    @staticmethod
    def get_track_points(dto: TrackPointRequestDTO) -> TrackPointResponseDTO:
        # Получение автомобиля
        try:
            vehicle = Vehicle.objects.select_related('enterprise').get(id=dto.vehicle_id)
        except Vehicle.DoesNotExist:
            raise ValidationError("Vehicle not found")

        # Парсинг временных меток и перевод их в UTC
        try:
            start_time = parse_datetime(dto.start_time).astimezone(ZoneInfo("UTC"))
            end_time = parse_datetime(dto.end_time).astimezone(ZoneInfo("UTC"))
        except Exception as e:
            raise ValidationError(f"Invalid date format: {e}")

        # Фильтрация точек трека
        tracks = TrackPoint.objects.filter(
            vehicle=vehicle,
            timestamp__range=(start_time, end_time)
        )

        # Получение предприятия и часовой зоны
        enterprise = vehicle.enterprise
        local_tz = ZoneInfo(enterprise.timezone)

        if dto.output_format == "geojson":
            # Формирование GeoJSON
            track_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": track.location.coords
                        },
                        "properties": {
                            "timestamp": track.timestamp.astimezone(local_tz).isoformat()
                        }
                    }
                    for track in tracks
                ]
            }
        else:
            # Формирование обычного JSON
            track_data = [
                {
                    "location": track.location.coords,
                    "timestamp": track.timestamp.astimezone(local_tz).isoformat(),
                }
                for track in tracks
            ]

        return TrackPointResponseDTO(data=track_data)


class TripService:
    @staticmethod
    def get_trip_summary(dto: TripSummaryRequestDTO) -> List[TripSummaryDTO]:
        # Получаем ТС
        try:
            vehicle = Vehicle.objects.get(id=dto.vehicle_id)
        except Vehicle.DoesNotExist:
            raise ValidationError("Транспортное средство не найдено")

        enterprise = vehicle.enterprise
        # Присваиваем таймзону предприятия входным датам
        local_tz = ZoneInfo(enterprise.timezone)
        local_start = datetime.fromisoformat(dto.start_time).replace(tzinfo=local_tz)
        local_end = datetime.fromisoformat(dto.end_time).replace(tzinfo=local_tz)

        # Переводим локальное время в UTC
        start_date_utc = local_start.astimezone(ZoneInfo("UTC"))
        end_date_utc = local_end.astimezone(ZoneInfo("UTC"))

        # Фильтруем поездки по указанному интервалу
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date_utc,
            end_time__lte=end_date_utc
        )

        result = []
        for trip in trips:
            # Получаем точки трека
            track_points = TrackPoint.objects.filter(
                vehicle=vehicle,
                timestamp__gte=trip.start_time,
                timestamp__lte=trip.end_time
            ).order_by('timestamp')

            # Преобразуем время в локальное
            local_start_time = enterprise.to_local_time(trip.start_time)
            local_end_time = enterprise.to_local_time(trip.end_time)

            if track_points.exists():
                start_point = track_points.first()
                end_point = track_points.last()
                start_address = get_address_for_point(start_point.location)
                end_address = get_address_for_point(end_point.location)

                result.append(TripSummaryDTO(
                    start_time_local=local_start_time.isoformat(),
                    end_time_local=local_end_time.isoformat(),
                    duration=str(trip.duration) if trip.duration else None,
                    start_location=[start_point.location.y, start_point.location.x],
                    start_address=start_address,
                    end_location=[end_point.location.y, end_point.location.x],
                    end_address=end_address
                ))
            else:
                # Если нет точек трека
                result.append(TripSummaryDTO(
                    start_time_local=local_start_time.isoformat(),
                    end_time_local=local_end_time.isoformat(),
                    duration=str(trip.duration) if trip.duration else None,
                    start_location=None,
                    start_address=None,
                    end_location=None,
                    end_address=None
                ))

        return result


class VehicleDetailService:
    @staticmethod
    def get_context(dto: VehicleDetailDTO) -> dict:
        vehicle = Vehicle.objects.get(id=dto.vehicle_id)
        context = {
            'start_value': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
            'end_value': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'trip_list': [],
            'trip_data_json': '[]'
        }

        if dto.start_time and dto.end_time:
            try:
                # Фильтрация поездок
                trips = TripService._get_filtered_trips(vehicle, dto.start_time, dto.end_time)
                trip_list, trip_data = VehicleDetailService._process_trips(vehicle, trips)
                context.update({
                    'start_value': dto.start_time,
                    'end_value': dto.end_time,
                    'trip_list': trip_list,
                    'trip_data_json': json.dumps(trip_data, ensure_ascii=False)
                })
            except Exception:
                pass

        return context

    @staticmethod
    def _get_filtered_trips(vehicle, start_time, end_time):
        local_tz = ZoneInfo(vehicle.enterprise.timezone)
        local_start = datetime.fromisoformat(start_time).replace(tzinfo=local_tz)
        local_end = datetime.fromisoformat(end_time).replace(tzinfo=local_tz)

        start_utc = local_start.astimezone(ZoneInfo("UTC"))
        end_utc = local_end.astimezone(ZoneInfo("UTC"))

        return Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_utc,
            end_time__lte=end_utc
        ).order_by('start_time')

    @staticmethod
    def _process_trips(vehicle, trips):
        colors = ["red", "blue", "green", "orange", "purple"]
        trip_list = []
        trip_data = []

        for idx, trip in enumerate(trips):
            color = colors[idx % len(colors)]
            track_points = TrackPoint.objects.filter(
                vehicle=vehicle,
                timestamp__gte=trip.start_time,
                timestamp__lte=trip.end_time
            ).order_by('timestamp')

            local_start_time = vehicle.enterprise.to_local_time(trip.start_time)
            local_end_time = vehicle.enterprise.to_local_time(trip.end_time)

            if track_points.exists():
                start_point = track_points.first()
                end_point = track_points.last()

                trip_list.append({
                    "color": color,
                    "start_time_local": local_start_time.strftime('%d.%m.%Y %H:%M'),
                    "end_time_local": local_end_time.strftime('%d.%m.%Y %H:%M'),
                    "duration": str(trip.duration) if trip.duration else None,
                    "start_address": get_address_for_point(start_point.location),
                    "end_address": get_address_for_point(end_point.location)
                })

                trip_data.append({
                    "trip_id": trip.id,
                    "color": color,
                    "start_time": local_start_time.strftime('%d.%m.%Y %H:%M'),
                    "end_time": local_end_time.strftime('%d.%m.%Y %H:%M'),
                    "coords": [[tp.location.y, tp.location.x] for tp in track_points]
                })

        return trip_list, trip_data


class ReportService:
    @staticmethod
    def generate_report(dto: ReportRequestDTO) -> dict:
        try:
            start_date = datetime.strptime(dto.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(dto.end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return {"error": "Неверный формат дат"}

        if dto.report_type == 'car_mileage':
            if not dto.vehicle_id:
                return {"error": "Не указан vehicle_id"}
            try:
                report = generate_car_mileage_report(dto.vehicle_id, start_date, end_date, dto.period)
                return report.result
            except Vehicle.DoesNotExist:
                return {"error": "Транспортное средство не найдено"}

        elif dto.report_type == 'driver_time':
            if not dto.driver_id:
                return {"error": "Не указан driver_id"}
            try:
                report = generate_driver_time_report(dto.driver_id, start_date, end_date, dto.period)
                return report.result
            except Driver.DoesNotExist:
                return {"error": "Водитель не найден"}

        elif dto.report_type == 'enterprise_active_cars':
            if not dto.enterprise_id:
                return {"error": "Не указан enterprise_id"}
            try:
                report = generate_enterprise_active_cars_report(dto.enterprise_id, start_date, end_date, dto.period)
                return report.result
            except Enterprise.DoesNotExist:
                return {"error": "Предприятие не найдено"}

        else:
            return {"error": "Неизвестный тип отчёта"}


class TripUploadService:
    @staticmethod
    def upload_trip(dto: TripUploadDTO):
        vehicle = Vehicle.objects.get(id=dto.vehicle_id)

        # Проверка конфликта поездок
        if vehicle.trips.filter(start_time__lt=dto.end_time, end_time__gt=dto.start_time).exists():
            raise ValidationError("Новая поездка конфликтует с существующей.")

        # Парсинг GPX файла
        try:
            gpx_content = dto.gpx_file.decode('utf-8')
            gpx = gpxpy.parse(gpx_content)
            track_points_list = []

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time is None or not (dto.start_time <= point.time <= dto.end_time):
                            raise ValidationError(
                                "Все точки трека должны иметь время и находиться в заданном диапазоне.")
                        geo_point = Point(point.longitude, point.latitude)
                        track_points_list.append({
                            'timestamp': point.time,
                            'location': geo_point,
                        })
        except Exception as e:
            raise ValidationError(f"Ошибка при обработке GPX файла: {e}")

        # Создание поездки
        trip = Trip.objects.create(
            vehicle=vehicle,
            start_time=dto.start_time,
            end_time=dto.end_time,
            gpx_file=dto.gpx_file,
        )

        # Создание точек трека
        if track_points_list:
            track_points_objects = [
                TrackPoint(
                    vehicle=vehicle,
                    timestamp=tp['timestamp'],
                    location=tp['location']
                )
                for tp in track_points_list
            ]
            TrackPoint.objects.bulk_create(track_points_objects)

        return trip