import zoneinfo
import os
import json
import io
import zipfile
import gpxpy
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from rest_framework import viewsets, status
from rest_framework.views import APIView
from .permissions import IsManagerOrReadOnly
from .forms import ManagerLoginForm, VehicleForm, ReportForm, TripUploadForm
from .models import Vehicle, Enterprise, Driver, TrackPoint, Trip, Report
from .serializers import VehicleSerializer, EnterpriseSerializer, DriverSerializer, CustomAuthTokenSerializer, \
    TrackPointSerializer
from .resources import EnterpriseResource, VehicleResource, TripResource
from .pagination import CustomVehiclePagination
from .utils import get_address_for_point, generate_car_mileage_report, generate_driver_time_report, generate_enterprise_active_cars_report
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, FileResponse
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from django.db.models import Q
from django.views.generic import DetailView
from tablib import Databook


class EnterpriseViewSet(viewsets.ModelViewSet):
    serializer_class = EnterpriseSerializer
    permission_classes = [IsManagerOrReadOnly]
    #
    def get_queryset(self):
        user = self.request.user
        
        # Если пользователь — суперпользователь, возвращаем все предприятия
        if user.is_superuser:
            return Enterprise.objects.all()
            
        # Если пользователь - менеджер, возвращаем только доступные предприятия
        if hasattr(user, 'manager'):
            return Enterprise.objects.filter(managers=user.manager)
        return Enterprise.objects.none()  # Пустой список для других пользователей


class EnterpriseListView(ListView):
    model = Enterprise
    template_name = 'cars/enterprises_list.html'
    context_object_name = 'enterprises'

    def get_queryset(self):
        # Получение queryset из EnterpriseViewSet
        viewset = EnterpriseViewSet()
        viewset.request = self.request  # Передаём запрос
        return viewset.get_queryset()

    def post(self, request, *args, **kwargs):
        # Обработка изменения таймзон для предприятий
        for enterprise in self.get_queryset():
            timezone_field = f"timezone_{enterprise.id}"
            new_timezone = request.POST.get(timezone_field)
            try:
                enterprise.timezone = ZoneInfo(new_timezone)  # Проверка и сохранение
                enterprise.save()
            except (zoneinfo.ZoneInfoNotFoundError, ValueError):
                pass  # Если таймзона некорректна, пропускаем
        return redirect('cars:enterprises_list')  # Редирект на ту же страницу после изменений

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передача всех доступных таймзон в шаблон
        context['timezones'] = [tz for tz in zoneinfo.available_timezones()]
        return context


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [IsManagerOrReadOnly]
    pagination_class = CustomVehiclePagination

    def get_queryset(self):
        user = self.request.user

        # Фильтруем машины по предприятиям, доступным менеджеру
        if hasattr(user, 'manager'):
            return Vehicle.objects.filter(enterprise__in=user.manager.enterprises.all())

        # Если пользователь не менеджер, возвращаем пустой QuerySet
        return Vehicle.objects.none()

    def get_object(self):
        user = self.request.user
        
        try:
            obj = Vehicle.objects.get(pk=self.kwargs['pk'])
        except Vehicle.DoesNotExist:
            # Возвращаем 403, если автомобиль не найден
            raise PermissionDenied("ACCESS DENIED")

        # Проверка доступа для менеджера
        if hasattr(user, 'manager') and obj.enterprise not in user.manager.enterprises.all():
            raise PermissionDenied("ACCESS DENIED")
        
        return obj


class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    permission_classes = [IsManagerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser:
            return Driver.objects.all()
            
        # Фильтруем водителей по предприятиям, доступным менеджеру
        if hasattr(user, 'manager'):
            return Driver.objects.filter(enterprise__in=user.manager.enterprises.all())
        return Driver.objects.none()
        
        
@csrf_protect
def test(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        return JsonResponse({"message": "Данные получены", "data": data})
    return render(request, 'test.html')
    
    
    # Для получения токена и ошибки, если введеные данные неверны, или пароль неверный
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data)
        
        # Валидация введенных данных
        if serializer.is_valid():
            user = authenticate(
	        username=serializer.validated_data['username'],
	        password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key})
            else:
                return Response(
	            {"detail": "Invalid credentials"},
	            status=status.HTTP_401_UNAUTHORIZED
	        )
        return Response(
            {"detail": "Invalid request"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
class ManagerLoginView(LoginView):
    template_name = 'cars/login.html'
    authentication_form = ManagerLoginForm

    def get_success_url(self):
        # После успешной авторизации перенаправляем на страницу доступных предприятий
        return reverse('cars:enterprises_list')
        
        
class VehicleManageView(TemplateView):
    template_name = 'cars/manage_vehicles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enterprise_id = kwargs.get('enterprise_id')
        enterprise = get_object_or_404(Enterprise, id=enterprise_id)

        vehicles = enterprise.vehicles.all()

        paginator = Paginator(vehicles, 30)  # Пагинация: 30 записей на страницу
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['enterprise'] = enterprise
        context['page_obj'] = page_obj
        context['vehicle_form'] = VehicleForm()
        return context

    @login_required()
    def post(self, request, *args, **kwargs):
        enterprise_id = kwargs.get('enterprise_id')
        enterprise = get_object_or_404(Enterprise, id=enterprise_id)

        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.enterprise = enterprise
            vehicle.save()
            return redirect('cars:manage_vehicles', enterprise_id=enterprise.id)
        else:
            context = self.get_context_data(**kwargs)
            context['vehicle_form'] = form
            return self.render_to_response(context)
            
class VehicleEditView(UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'cars/edit_vehicle.html'
    success_url = reverse_lazy('cars:enterprises_list')

class VehicleDeleteView(DeleteView):
    model = Vehicle
    template_name = 'cars/delete_vehicle.html'
    success_url = reverse_lazy('cars:enterprises_list')


class TrackPointView(APIView):
    def get(self, request, vehicle_id):
        # Получение автомобиля
        try:
            vehicle = Vehicle.objects.select_related('enterprise').get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            raise NotFound("Vehicle not found")

        # Получение предприятия и часовой зоны
        enterprise = vehicle.enterprise
        local_tz = ZoneInfo(enterprise.timezone)

        # Параметры диапазона времени
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        output_format = request.query_params.get('f')

        if output_format not in ['json', 'geojson']:
            return Response({'error': 'Invalid format request'}, status=status.HTTP_400_BAD_REQUEST)

        if not start_time or not end_time:
            raise ValidationError("Both 'start_time' and 'end_time' are required.")

        # Парсинг временных меток и перевод их в UTC
        try:
            start_time = parse_datetime(start_time).astimezone(ZoneInfo("UTC"))
            end_time = parse_datetime(end_time).astimezone(ZoneInfo("UTC"))
        except Exception as e:
            raise ValidationError(f"Invalid date format: {e}")

        # Фильтрация точек трека
        tracks = TrackPoint.objects.filter(
            vehicle=vehicle,
            timestamp__range=(start_time, end_time)
        )

        if output_format == "geojson":
            # Возвращаем GeoJSON
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
            # Возвращаем обычный JSON
            track_data = [
                {
                    "location": track.location.coords,
                    "timestamp": track.timestamp.astimezone(local_tz).isoformat(),
                }
                for track in tracks
            ]

        return Response(track_data)
        
        
class TripAPI(APIView):
    def get(self, request, vehicle_id):
        # 1. Извлечение и валидация параметров запроса 'start' и 'end' как дат в формате ISO.
        #    Если формат неверный или отсутствует, возвращаем ошибку.
        try:
            start_date = datetime.fromisoformat(request.query_params.get('start'))
            end_date = datetime.fromisoformat(request.query_params.get('end'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Некорректный формат 'start' или 'end'. Используйте ISO 8601 (например: 2023-01-01T12:00:00)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Получение объекта транспортного средства по его идентификатору.
        #    Если ТС не найдено, возвращаем ошибку.
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Транспортное средство не найдено."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Поиск маршрутов, которые полностью укладываются в заданный временной диапазон.
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date,
            end_time__lte=end_date
        )

        # 4. Если маршруты не найдены, возвращаем сообщение об их отсутствии.
        if not trips.exists():
            return Response(
                ["За указанный промежуток времени маршруты не найдены."], 
                status=status.HTTP_200_OK
            )

        # 5. Получение всех точек трека, соответствующих найденным маршрутам.
        #    Формируем Q-объект для фильтрации точек по временным интервалам всех маршрутов.
        trip_intervals = Q()
        for trip in trips:
            trip_intervals |= Q(timestamp__gte=trip.start_time, timestamp__lte=trip.end_time)

        track_points = TrackPoint.objects.filter(Q(vehicle=vehicle) & trip_intervals)

        # 6. Сериализация найденных точек трека и возврат их клиенту.
        serializer = TrackPointSerializer(track_points, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
       
class TripSummaryAPI(APIView):
    def get(self, request, vehicle_id):
        # 1. Извлекаем параметры, считаем, что они в локальном времени предприятия
        try:
            local_start = datetime.fromisoformat(request.query_params.get('start'))  # наивный datetime
            local_end = datetime.fromisoformat(request.query_params.get('end'))      # наивный datetime
        except (TypeError, ValueError):
            return Response(
                {"error": "Некорректный формат 'start' или 'end'. Используйте ISO 8601 (например: 2023-01-01T12:00:00)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Получаем ТС
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Транспортное средство не найдено."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        enterprise = vehicle.enterprise
        # Присваиваем таймзону предприятия входным датам
        local_tz = ZoneInfo(enterprise.timezone)
        local_start = local_start.replace(tzinfo=local_tz)
        local_end = local_end.replace(tzinfo=local_tz)

        # Переводим локальное время в UTC
        start_date_utc = local_start.astimezone(ZoneInfo("UTC"))
        end_date_utc = local_end.astimezone(ZoneInfo("UTC"))

        # 3. Фильтруем поездки по указанному интервалу
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date_utc,
            end_time__lte=end_date_utc
        )

        if not trips.exists():
            return Response(
                ["Поездки за указанный период не найдены."], 
                status=status.HTTP_200_OK
            )

        result = []
        for trip in trips:
            # Получаем точки трека, чтобы определить начальную и конечную локацию
            track_points = TrackPoint.objects.filter(
                vehicle=vehicle,
                timestamp__gte=trip.start_time,
                timestamp__lte=trip.end_time
            ).order_by('timestamp')

            if track_points.exists():
                start_point = track_points.first()
                end_point = track_points.last()
                start_address = get_address_for_point(start_point.location)
                end_address = get_address_for_point(end_point.location)

                # Преобразуем время старта/окончания поездки в локальное время для вывода
                local_start_time = enterprise.to_local_time(trip.start_time)
                local_end_time = enterprise.to_local_time(trip.end_time)

                result.append({
                    "start_time_local": local_start_time.isoformat(),
                    "end_time_local": local_end_time.isoformat(),
                    "duration": str(trip.duration) if trip.duration else None,
                    "start_location": [start_point.location.y, start_point.location.x],
                    "start_address": start_address,
                    "end_location": [end_point.location.y, end_point.location.x],
                    "end_address": end_address
                })
            else:
                # Если нет точек трека, укажем только время без локаций
                local_start_time = enterprise.to_local_time(trip.start_time)
                local_end_time = enterprise.to_local_time(trip.end_time)
                result.append({
                    "start_time_local": local_start_time.isoformat(),
                    "end_time_local": local_end_time.isoformat(),
                    "duration": str(trip.duration) if trip.duration else None,
                    "start_location": None,
                    "start_address": None,
                    "end_location": None,
                    "end_address": None
                })

        return Response(result, status=status.HTTP_200_OK)



class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'cars/vehicle_info.html'
    context_object_name = 'vehicle'
    pk_url_kwarg = 'pk'  # если в urls.py: path('vehicles/<int:pk>/info/', ...)

    def get_context_data(self, **kwargs):
        """
        1) Предзаполнить последние 30 дней в полях (24ч формат без am/pm)
        2) Не показывать поездки, пока пользователь не нажмёт "Показать"
        3) Если есть GET-параметры start/end, фильтровать поездки, рисовать на карте
        4) Каждой поездке присвоить цвет.
        """
        context = super().get_context_data(**kwargs)
        vehicle = self.object

        # ---------- 1. Даты по умолчанию: последние 30 дней ----------
        now = timezone.now()
        default_start = now - timedelta(days=30)

        # Эти две переменные пойдут в <input type="datetime-local">
        # Формат YYYY-MM-DDTHH:MM (24ч без am/pm)
        context['start_value'] = default_start.strftime('%Y-%m-%dT%H:%M')
        context['end_value'] = now.strftime('%Y-%m-%dT%H:%M')

        # Считываем GET-параметры
        start_str = self.request.GET.get('start')
        end_str = self.request.GET.get('end')

        # Пока не нажали "Показать", поездки не фильтруем
        trip_list = []
        trip_data = []

        if start_str and end_str:
            # Пользователь отправил форму, пытаемся распарсить
            try:
                local_start_naive = datetime.fromisoformat(start_str)  # наивный datetime
                local_end_naive = datetime.fromisoformat(end_str)
            except ValueError:
                # Если пользователь ввёл некорректно, тогда оставим дефолты
                local_start_naive = default_start
                local_end_naive = now
            
            # Чтобы инпуты сохраняли введённые значения
            context['start_value'] = local_start_naive.strftime('%Y-%m-%dT%H:%M')
            context['end_value'] = local_end_naive.strftime('%Y-%m-%dT%H:%M')

            # -------- Локальная таймзона предприятия --------
            enterprise = vehicle.enterprise
            if enterprise and enterprise.timezone:
                local_tz = ZoneInfo(enterprise.timezone)
            else:
                local_tz = ZoneInfo("UTC")

            local_start = local_start_naive.replace(tzinfo=local_tz)
            local_end = local_end_naive.replace(tzinfo=local_tz)

            # Переводим в UTC для фильтра
            start_utc = local_start.astimezone(ZoneInfo("UTC"))
            end_utc = local_end.astimezone(ZoneInfo("UTC"))

            # -------- Фильтруем поездки --------
            trips = Trip.objects.filter(
                vehicle=vehicle,
                start_time__gte=start_utc,
                end_time__lte=end_utc
            ).order_by('start_time')

            colors = ["red", "blue", "green", "orange", "purple"]
            for idx, trip in enumerate(trips):
                # Для каждой поездки получаем список точек
                track_points = TrackPoint.objects.filter(
                    vehicle=vehicle,
                    timestamp__gte=trip.start_time,
                    timestamp__lte=trip.end_time
                ).order_by('timestamp')

                # Получаем локальные время старта/конца (для отображения)
                local_start_time = enterprise.to_local_time(trip.start_time)
                local_end_time = enterprise.to_local_time(trip.end_time)

                # Назначаем цвет
                color = colors[idx % len(colors)]

                if track_points.exists():
                    start_point = track_points.first()
                    end_point = track_points.last()

                    start_address = get_address_for_point(start_point.location)
                    end_address = get_address_for_point(end_point.location)

                    trip_list.append({
                        "color": color,
                        "start_time_local": local_start_time.strftime('%d.%m.%Y %H:%M'),
                        "end_time_local": local_end_time.strftime('%d.%m.%Y %H:%M'),
                        "duration": str(trip.duration) if trip.duration else None,
                        "start_address": start_address,
                        "end_address": end_address
                    })

                    # Для карты Leaflet — собираем координаты
                    coords = []
                    for tp in track_points:
                        coords.append([tp.location.y, tp.location.x])  # lat, lon
                    trip_data.append({
                        "trip_id": trip.id,
                        "color": color,
                        "start_time": local_start_time.strftime('%d.%m.%Y %H:%M'),
                        "end_time": local_end_time.strftime('%d.%m.%Y %H:%M'),
                        "coords": coords
                    })
                else:
                    # Нет точек трека
                    trip_list.append({
                        "color": color,
                        "start_time_local": local_start_time.strftime('%d.%m.%Y %H:%M'),
                        "end_time_local": local_end_time.strftime('%d.%m.%Y %H:%M'),
                        "duration": str(trip.duration) if trip.duration else None,
                        "start_address": None,
                        "end_address": None
                    })
                    trip_data.append({
                        "trip_id": trip.id,
                        "color": color,
                        "start_time": local_start_time.strftime('%d.%m.%Y %H:%M'),
                        "end_time": local_end_time.strftime('%d.%m.%Y %H:%M'),
                        "coords": []
                    })

        # Список поездок + данные для карты
        context["trip_list"] = trip_list
        context["trip_data_json"] = json.dumps(trip_data, ensure_ascii=False)

        return context

# Экспорт данных предприятия
def export_data(request):
    print("DEBUG: export_data called with GET:", request.GET)

    enterprise_id = request.GET.get('enterprise_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    file_format = request.GET.get('file_format', 'json')

    enterprise = get_object_or_404(Enterprise, pk=enterprise_id)

    # Парсим даты
    date_format = "%Y-%m-%d"
    start_date = datetime.strptime(start_str, date_format) if start_str else None
    end_date = datetime.strptime(end_str, date_format) if end_str else None

    # Готовим queryset
    enterprise_qs = Enterprise.objects.filter(id=enterprise.id)
    vehicles_qs = Vehicle.objects.filter(enterprise=enterprise)
    trips_qs = Trip.objects.filter(vehicle__enterprise=enterprise)

    # Если передан диапазон, фильтруем Trips
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

    # Выдаем JSON
    if file_format == 'json':
        book = Databook()
        ent_dataset.title = "Enterprise"
        veh_dataset.title = "Vehicle"
        trip_dataset.title = "Trip"
        book.add_sheet(ent_dataset)
        book.add_sheet(veh_dataset)
        book.add_sheet(trip_dataset)
        # Получаем одну строку JSON
        json_data = book.json
        response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="export.json"'
        return response
    else:
        # CSV -> делаем zip с тремя файлами
        ent_csv = ent_dataset.csv
        veh_csv = veh_dataset.csv
        trip_csv = trip_dataset.csv

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("enterprise.csv", ent_csv)
            zf.writestr("vehicles.csv", veh_csv)
            zf.writestr("trips.csv", trip_csv)

        memory_file.seek(0)
        response = FileResponse(memory_file, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="export_csv.zip"'
        return response
        
# Импорт данных по предприятию
def import_data(request):
    if request.method == 'POST':
        file = request.FILES.get('file_import')
        if not file:
            return HttpResponse("Файл не выбран", status=400)

        # Определяем тип
        fn = file.name.lower()
        if fn.endswith('.json'):
            return _import_json(file)
        elif fn.endswith('.zip'):
            return _import_csv_zip(file)
        else:
            return HttpResponse("Неподдерживаемый формат (ожидается .json или .zip)", status=400)
    else:
        return HttpResponse("Используйте POST", status=405)

def _import_json(file):
    from .resources import EnterpriseResource, VehicleResource, TripResource
    from tablib import Databook

    content = file.read().decode('utf-8')
    try:
        book = Databook()
        book.json = content  # загружаем из JSON
    except Exception as e:
        return HttpResponse(f"Ошибка при чтении JSON: {e}", status=400)

    # book должен иметь sheets: Enterprise, Vehicle, Trip
    sheets = {sheet.title: sheet for sheet in book.sheets()}

    ent_res = EnterpriseResource()
    veh_res = VehicleResource()
    trip_res = TripResource()

    # 1. Enterprise
    ent_sheet = sheets.get("Enterprise")
    if ent_sheet:
        result_ent = ent_res.import_data(ent_sheet, dry_run=True)
        if result_ent.has_errors():
            return HttpResponse(f"Ошибки при импорте Enterprise: {result_ent.row_errors()}", status=400)
        ent_res.import_data(ent_sheet, dry_run=False)

    # 2. Vehicle
    veh_sheet = sheets.get("Vehicle")
    if veh_sheet:
        result_veh = veh_res.import_data(veh_sheet, dry_run=True)
        if result_veh.has_errors():
            return HttpResponse(f"Ошибки при импорте Vehicles: {result_veh.row_errors()}", status=400)
        veh_res.import_data(veh_sheet, dry_run=False)

    # 3. Trip
    trip_sheet = sheets.get("Trip")
    if trip_sheet:
        result_trip = trip_res.import_data(trip_sheet, dry_run=True)
        if result_trip.has_errors():
            return HttpResponse(f"Ошибки при импорте Trips: {result_trip.row_errors()}", status=400)
        trip_res.import_data(trip_sheet, dry_run=False)

    return HttpResponse("Импорт JSON завершён")

def _import_csv_zip(file):
    import zipfile
    from .resources import EnterpriseResource, VehicleResource, TripResource

    if not zipfile.is_zipfile(file):
        return HttpResponse("Загруженный файл не является ZIP", status=400)

    with zipfile.ZipFile(file, 'r') as zf:
        # Проверим, есть ли наши файлы
        needed_files = {"enterprise.csv", "vehicles.csv", "trips.csv"}
        files_in_zip = set(zf.namelist())
        if not needed_files.issubset(files_in_zip):
            return HttpResponse(f"Необходимые CSV-файлы не найдены: {needed_files - files_in_zip}", status=400)

        ent_csv = zf.read("enterprise.csv").decode('utf-8')
        veh_csv = zf.read("vehicles.csv").decode('utf-8')
        trip_csv = zf.read("trips.csv").decode('utf-8')

        ent_res = EnterpriseResource()
        veh_res = VehicleResource()
        trip_res = TripResource()

        # Enterprise
        result_ent = ent_res.import_data(ent_csv, format='csv', dry_run=True)
        if result_ent.has_errors():
            return HttpResponse(f"Ошибки при импорте Enterprise: {result_ent.row_errors()}", status=400)
        ent_res.import_data(ent_csv, format='csv', dry_run=False)

        # Vehicles
        result_veh = veh_res.import_data(veh_csv, format='csv', dry_run=True)
        if result_veh.has_errors():
            return HttpResponse(f"Ошибки при импорте Vehicles: {result_veh.row_errors()}", status=400)
        veh_res.import_data(veh_csv, format='csv', dry_run=False)

        # Trips
        result_trip = trip_res.import_data(trip_csv, format='csv', dry_run=True)
        if result_trip.has_errors():
            return HttpResponse(f"Ошибки при импорте Trips: {result_trip.row_errors()}", status=400)
        trip_res.import_data(trip_csv, format='csv', dry_run=False)

    return HttpResponse("Импорт CSV (ZIP) завершён")


@api_view(['GET'])
def report_api(request):
    """
    Пример: GET /cars/report-api/?report_type=car_mileage&vehicle_id=44&start=2024-12-01&end=2025-01-13&period=month
    """
    report_type = request.GET.get('report_type')
    period = request.GET.get('period', 'day')
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({"error": "Неверный формат дат"}, status=status.HTTP_400_BAD_REQUEST)

    if report_type == 'car_mileage':
        vehicle_id = request.GET.get('vehicle_id')
        if not vehicle_id:
            return Response({"error": "Не указан vehicle_id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            report = generate_car_mileage_report(vehicle_id, start_date, end_date, period)
            return Response(report.result, status=status.HTTP_200_OK)
        except Vehicle.DoesNotExist:
            return Response({"error": "Транспортное средство не найдено"}, status=status.HTTP_404_NOT_FOUND)

    elif report_type == 'driver_time':
        driver_id = request.GET.get('driver_id')
        if not driver_id:
            return Response({"error": "Не указан driver_id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            report = generate_driver_time_report(driver_id, start_date, end_date, period)
            return Response(report.result, status=status.HTTP_200_OK)
        except Driver.DoesNotExist:
            return Response({"error": "Водитель не найден"}, status=status.HTTP_404_NOT_FOUND)

    elif report_type == 'enterprise_active_cars':
        enterprise_id = request.GET.get('enterprise_id')
        if not enterprise_id:
            return Response({"error": "Не указан enterprise_id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            report = generate_enterprise_active_cars_report(enterprise_id, start_date, end_date, period)
            return Response(report.result, status=status.HTTP_200_OK)
        except Enterprise.DoesNotExist:
            return Response({"error": "Предприятие не найдено"}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Неизвестный тип отчёта"}, status=status.HTTP_400_BAD_REQUEST)


def reports_list(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            period = form.cleaned_data['period']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            try:
                if report_type == 'car_mileage':
                    vehicle = form.cleaned_data['vehicle']
                    report = generate_car_mileage_report(vehicle.id, start_date, end_date, period)
                elif report_type == 'driver_time':
                    driver = form.cleaned_data['driver']
                    report = generate_driver_time_report(driver.id, start_date, end_date, period)
                elif report_type == 'enterprise_active_cars':
                    enterprise = form.cleaned_data['enterprise']
                    report = generate_enterprise_active_cars_report(enterprise.id, start_date, end_date, period)
                else:
                    messages.error(request, "Неизвестный тип отчёта.")
                    return redirect('cars:reports_list')

                messages.success(request, f"Отчёт '{report.name}' успешно создан.")
                return redirect('cars:reports_list')

            except Exception as e:
                messages.error(request, f"Ошибка при создании отчёта: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ReportForm()

    reports = Report.objects.all().order_by('-created_at')  # Сортировка по убыванию даты создания
    context = {
        'form': form,
        'reports': reports,
    }

    return render(request, 'cars/reports_list.html', context)
    
    
def view_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return JsonResponse(report.result, safe=False)
    
def upload_trip(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        form = TripUploadForm(request.POST, request.FILES)
        if form.is_valid():
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            gpx_file = request.FILES['gpx_file']
            
            # Проверяем, чтобы поездка не перекрывалась с существующими
            if vehicle.trips.filter(start_time__lt=end_time, end_time__gt=start_time).exists():
                form.add_error(None, "Новая поездка конфликтует с существующей.")
            else:
                try:
                    # Читаем содержимое файла и сбрасываем указатель
                    gpx_content = gpx_file.read().decode('utf-8')
                    gpx_file.seek(0)
                    gpx = gpxpy.parse(gpx_content)
                    track_points_list = []  # Список для сохранения данных точек
                    
                    # Проходим по всем точкам трека
                    for track in gpx.tracks:
                        for segment in track.segments:
                            for point in segment.points:
                                if point.time is None or not (start_time <= point.time <= end_time):
                                    form.add_error('gpx_file', "Все точки трека должны иметь время и находиться в заданном диапазоне.")
                                    break
                                # Создаем объект Point (GeoDjango ожидает координаты в формате (долгота, широта))
                                geo_point = Point(point.longitude, point.latitude)
                                track_points_list.append({
                                    'timestamp': point.time,
                                    'location': geo_point,
                                })
                except Exception as e:
                    form.add_error('gpx_file', f"Ошибка при обработке GPX файла: {e}")
            
            if not form.errors:
                # Создаем объект поездки
                trip = Trip.objects.create(
                    vehicle=vehicle,
                    start_time=start_time,
                    end_time=end_time,
                    gpx_file=gpx_file,
                )
                # Создаем объекты TrackPoint для каждой точки маршрута
                track_points_objects = [
                    TrackPoint(
                        vehicle=vehicle,
                        timestamp=tp['timestamp'],
                        location=tp['location']
                    )
                    for tp in track_points_list
                ]
                if track_points_objects:
                    TrackPoint.objects.bulk_create(track_points_objects)
                messages.success(request, "Поездка успешно добавлена!")
                return redirect('cars:vehicle_info', pk=vehicle.id)
    else:
        form = TripUploadForm()
    
    return render(request, 'cars/upload_trip.html', {'form': form, 'vehicle': vehicle})
