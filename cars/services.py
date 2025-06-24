import zoneinfo
from typing import List, io
from zoneinfo import ZoneInfo
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from datetime import datetime, timedelta

from django.utils.dateparse import parse_datetime
from tablib import Databook

from .models import Vehicle, Enterprise, Trip, TrackPoint, Driver
from .resources import EnterpriseResource, VehicleResource, TripResource
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
        if not dto.start_date or not dto.end_date:
            return {"error": "Не указаны даты начала или окончания периода"}
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

class TripAPIService:
    @staticmethod
    def get_trips_track_points(vehicle_id, start_date, end_date):
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            raise NotFound("Транспортное средство не найдено")

        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date,
            end_time__lte=end_date
        )

        if not trips.exists():
            return []

        trip_intervals = Q()
        for trip in trips:
            trip_intervals |= Q(timestamp__gte=trip.start_time, timestamp__lte=trip.end_time)

        return TrackPoint.objects.filter(Q(vehicle=vehicle) & trip_intervals)


class ImportExportService:
    @staticmethod
    def export_data(enterprise_id, start_str, end_str, file_format):
        enterprise = Enterprise.objects.get(pk=enterprise_id)

        # Парсим даты
        date_format = "%Y-%m-%d"
        start_date = datetime.strptime(start_str, date_format) if start_str else None
        end_date = datetime.strptime(end_str, date_format) if end_str else None

        # Готовим queryset
        enterprise_qs = Enterprise.objects.filter(id=enterprise.id)
        vehicles_qs = Vehicle.objects.filter(enterprise=enterprise)
        trips_qs = Trip.objects.filter(vehicle__enterprise=enterprise)

        if start_date and end_date:
            trips_qs = trips_qs.filter(start_time__gte=start_date, end_time__lte=end_date)

        # Создаём ресурсы
        ent_res = EnterpriseResource()
        veh_res = VehicleResource()
        trip_res = TripResource()

        # Экспортируем
        ent_dataset = ent_res.export(enterprise_qs)
        veh_dataset = veh_res.export(vehicles_qs)
        trip_dataset = trip_res.export(trips_qs)

        return ent_dataset, veh_dataset, trip_dataset, file_format

    @staticmethod
    def handle_export_response(ent_dataset, veh_dataset, trip_dataset, file_format):
        if file_format == 'json':
            book = Databook()
            ent_dataset.title = "Enterprise"
            veh_dataset.title = "Vehicle"
            trip_dataset.title = "Trip"
            book.add_sheet(ent_dataset)
            book.add_sheet(veh_dataset)
            book.add_sheet(trip_dataset)
            json_data = book.json
            return HttpResponse(json_data, content_type='application/json; charset=utf-8'), 'export.json'
        else:
            ent_csv = ent_dataset.csv
            veh_csv = veh_dataset.csv
            trip_csv = trip_dataset.csv

            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("enterprise.csv", ent_csv)
                zf.writestr("vehicles.csv", veh_csv)
                zf.writestr("trips.csv", trip_csv)

            memory_file.seek(0)
            return memory_file, 'export_csv.zip'

    @staticmethod
    def import_json(file):
        content = file.read().decode('utf-8')
        book = Databook()
        book.json = content
        sheets = {sheet.title: sheet for sheet in book.sheets()}

        ent_res = EnterpriseResource()
        veh_res = VehicleResource()
        trip_res = TripResource()

        # 1. Enterprise
        if ent_sheet := sheets.get("Enterprise"):
            ent_res.import_data(ent_sheet, dry_run=False)

        # 2. Vehicle
        if veh_sheet := sheets.get("Vehicle"):
            veh_res.import_data(veh_sheet, dry_run=False)

        # 3. Trip
        if trip_sheet := sheets.get("Trip"):
            trip_res.import_data(trip_sheet, dry_run=False)

    @staticmethod
    def import_csv_zip(file):
        with zipfile.ZipFile(file, 'r') as zf:
            needed_files = {"enterprise.csv", "vehicles.csv", "trips.csv"}
            files_in_zip = set(zf.namelist())
            if not needed_files.issubset(files_in_zip):
                raise ValidationError(f"Необходимые CSV-файлы не найдены: {needed_files - files_in_zip}")

            ent_csv = zf.read("enterprise.csv").decode('utf-8')
            veh_csv = zf.read("vehicles.csv").decode('utf-8')
            trip_csv = zf.read("trips.csv").decode('utf-8')

            ent_res = EnterpriseResource()
            veh_res = VehicleResource()
            trip_res = TripResource()

            ent_res.import_data(ent_csv, format='csv', dry_run=False)
            veh_res.import_data(veh_csv, format='csv', dry_run=False)
            trip_res.import_data(trip_csv, format='csv', dry_run=False)


class ReportFormService:
    @staticmethod
    def create_report(form_data):
        report_type = form_data['report_type']
        period = form_data['period']
        start_date = form_data['start_date']
        end_date = form_data['end_date']

        if report_type == 'car_mileage':
            return generate_car_mileage_report(
                form_data['vehicle'].id,
                start_date,
                end_date,
                period
            )
        elif report_type == 'driver_time':
            return generate_driver_time_report(
                form_data['driver'].id,
                start_date,
                end_date,
                period
            )
        elif report_type == 'enterprise_active_cars':
            return generate_enterprise_active_cars_report(
                form_data['enterprise'].id,
                start_date,
                end_date,
                period
            )
        raise ValueError("Неизвестный тип отчёта")


class EnterpriseService:
    @staticmethod
    def update_timezones(queryset, post_data):
        for enterprise in queryset:
            timezone_field = f"timezone_{enterprise.id}"
            if new_timezone := post_data.get(timezone_field):
                try:
                    enterprise.timezone = ZoneInfo(new_timezone)
                    enterprise.save()
                except (zoneinfo.ZoneInfoNotFoundError, ValueError):
                    pass
    @staticmethod
    def get_enterprises_for_user(user):
        if user.is_superuser:
            return Enterprise.objects.all()
        if hasattr(user, 'manager'):
            return Enterprise.objects.filter(managers=user.manager)
        return Enterprise.objects.none()


class VehicleService:
    @staticmethod
    def create_vehicle(form_data, enterprise):
        vehicle = Vehicle(
            model=form_data['model'],
            license_plate=form_data['license_plate'],
            # ... другие поля ...
            enterprise=enterprise
        )
        vehicle.full_clean()  # Валидация модели
        vehicle.save()
        return vehicle
    @staticmethod
    def get_vehicles_for_user(user):
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'manager'):
            return Vehicle.objects.filter(enterprise__in=user.manager.enterprises.all())
        return Vehicle.objects.none()
    @staticmethod
    def get_vehicle_for_user(user, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            raise PermissionDenied("ACCESS DENIED")
        # Проверка доступа
        if user.is_superuser:
            return vehicle
        if hasattr(user, 'manager') and vehicle.enterprise in user.manager.enterprises.all():
            return vehicle
        raise PermissionDenied("ACCESS DENIED")