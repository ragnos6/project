import os
import io
import json
import zipfile
import zoneinfo
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.views.decorators.csrf import csrf_exempt
from .tasks import save_driver_data
from drf_yasg.utils import swagger_auto_schema

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.db.models import Q, Prefetch
from django.shortcuts import redirect
from drf_yasg import openapi

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from tablib import Databook

from .dto import (
    TrackPointRequestDTO,
    TripSummaryRequestDTO,
    VehicleDetailDTO,
    ReportRequestDTO,
    TripUploadDTO,
)
from .forms import ManagerLoginForm, VehicleForm, ReportForm, TripUploadForm
from .models import Vehicle, Enterprise, Driver, TrackPoint, Trip, Report
from .permissions import IsManagerOrReadOnly
from .serializers import (
    VehicleSerializer,
    EnterpriseSerializer,
    DriverSerializer,
    CustomAuthTokenSerializer,
    TrackPointSerializer,
    TripAPIRequestSerializer,
    TripSummaryRequestSerializer,
    AuthTokenResponseSerializer,
)
from .resources import EnterpriseResource, VehicleResource, TripResource
from .pagination import CustomVehiclePagination, CustomDriverPagination
from .services import (
    TrackService,
    TripService,
    VehicleDetailService,
    ReportService,
    TripUploadService,
    EnterpriseService,
    TripAPIService,
    ImportExportService,
    ReportFormService,
    DriverService,
    VehicleService,
)
from .utils import (
    generate_car_mileage_report,
    generate_driver_time_report,
    generate_enterprise_active_cars_report,
)



@method_decorator(cache_page(30), name='list')  # кэшируем список на 30 секунд
class EnterpriseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnterpriseSerializer
    permission_classes = [IsManagerOrReadOnly]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        qs = EnterpriseService.get_enterprises_for_user(user)
        return qs.select_related('region').prefetch_related('vehicles', 'managers')


class EnterpriseListView(ListView):
    model = Enterprise
    template_name = 'cars/enterprises_list.html'
    context_object_name = 'enterprises'

    def get_queryset(self):
        return EnterpriseService.get_enterprises_for_user(self.request.user)

    def post(self, request, *args, **kwargs):
        EnterpriseService.update_timezones(self.get_queryset(), request.POST)
        return redirect('cars:enterprises_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передача всех доступных таймзон в шаблон
        context['timezones'] = [tz for tz in zoneinfo.available_timezones()]
        return context


@method_decorator(cache_page(20), name='list')  # кэш списка машин
class VehicleViewSet(viewsets.ReadOnlyModelViewSet):  # если не редактируется — ReadOnly
    serializer_class = VehicleSerializer
    permission_classes = [IsManagerOrReadOnly]
    pagination_class = CustomVehiclePagination
    throttle_classes = [UserRateThrottle]
    
    @swagger_auto_schema(
        operation_summary="Список автомобилей",
        operation_description="Возвращает автомобили, доступные текущему пользователю.",
        tags=["Vehicles"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Детали автомобиля",
        operation_description="Возвращает один автомобиль по id.",
        tags=["Vehicles"],
    )
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    def get_queryset(self):
        user = self.request.user
        qs = VehicleService.get_vehicles_for_user(user)
        return qs.select_related('enterprise').prefetch_related('drivers')

    def get_object(self):
        # оптимизация: не вызываем ORM дважды
        return VehicleService.get_vehicle_for_user(self.request.user, self.kwargs['pk'])


@method_decorator(cache_page(20), name='list')  
class DriverViewSet(viewsets.ReadOnlyModelViewSet): 
    serializer_class = DriverSerializer
    permission_classes = [IsManagerOrReadOnly]
    pagination_class = CustomDriverPagination
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        qs = DriverService.get_drivers_for_user(user)
        return qs.select_related('enterprise').prefetch_related('vehicles')

    def get_object(self):
        return DriverService.get_driver_for_user(self.request.user, self.kwargs['pk'])

class CustomAuthToken(ObtainAuthToken):

    @swagger_auto_schema(
        operation_summary="Получить auth token",
        request_body=CustomAuthTokenSerializer,
        responses={
            status.HTTP_200_OK: AuthTokenResponseSerializer,
            status.HTTP_400_BAD_REQUEST: "Invalid request",
            status.HTTP_401_UNAUTHORIZED: "Invalid credentials",
        },
        tags=["Auth"],
    )
    
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
        return reverse('cars:enterprises_list')

class VehicleManageView(LoginRequiredMixin, TemplateView):
    template_name = 'cars/manage_vehicles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enterprise_id = kwargs.get('enterprise_id')
        enterprise = get_object_or_404(Enterprise, id=enterprise_id)

        vehicles = enterprise.vehicles.order_by('-id')  # новые сверху [web:44]

        paginator = Paginator(vehicles, 30)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['enterprise'] = enterprise
        context['page_obj'] = page_obj
        context['vehicle_form'] = VehicleForm()
        return context

    def post(self, request, *args, **kwargs):
        enterprise_id = kwargs.get('enterprise_id')
        enterprise = get_object_or_404(Enterprise, id=enterprise_id)
        form = VehicleForm(request.POST)

        if form.is_valid():
            try:
                VehicleService.create_vehicle(
                    form.cleaned_data,
                    enterprise
                )
                return redirect('cars:manage_vehicles', enterprise_id=enterprise.id)
            except Exception as e:
                form.add_error(None, f"Ошибка при создании: {str(e)}")

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

    def get_success_url(self):
        # сохраняем enterprise_id от удаляемого объекта для редиректа
        return reverse_lazy('cars:manage_vehicles', kwargs={'enterprise_id': self.object.enterprise_id})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        enterprise_id = self.object.enterprise_id

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, "Автомобиль удалён.")
            return response
        except Exception as e:
            messages.error(request, f"Ошибка при удалении: {e}")
            return redirect('cars:manage_vehicles', enterprise_id=enterprise_id)


class TrackPointView(APIView):
    def get(self, request, vehicle_id):
        dto = TrackPointRequestDTO(
            vehicle_id=vehicle_id,
            start_time=request.query_params.get('start_time'),
            end_time=request.query_params.get('end_time'),
            output_format=request.query_params.get('f', 'json')
        )

        try:
            result = TrackService.get_track_points(dto)
            return Response(result.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripAPI(APIView):
    throttle_classes = [UserRateThrottle]

    start_param = openapi.Parameter(
        "start", openapi.IN_QUERY,
        description="Начало периода (ISO 8601 datetime).",
        type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME,
        required=True
    )
    end_param = openapi.Parameter(
        "end", openapi.IN_QUERY,
        description="Конец периода (ISO 8601 datetime).",
        type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME,
        required=True
    )

    @swagger_auto_schema(
        operation_summary="Трекпоинты за период",
        operation_description="Возвращает список точек трека для автомобиля за период.",
        manual_parameters=[start_param, end_param],
        responses={
            status.HTTP_200_OK: TrackPointSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: "Invalid params",
            status.HTTP_404_NOT_FOUND: "Not found",
        },
        tags=["Trips"],
    )
    
    def get(self, request, vehicle_id):
        serializer = TripAPIRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data['start']
        end_date = serializer.validated_data['end']

        cache_key = f"trip_points:{vehicle_id}:{start_date}:{end_date}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            # получаем трекпоинты через сервис
            track_points = TripAPIService.get_trips_track_points(vehicle_id, start_date, end_date)
            serializer_tp = TrackPointSerializer(track_points, many=True)
            data = serializer_tp.data

            # кэшируем результат на 60 секунд
            cache.set(cache_key, data, timeout=60)

            return Response(data, status=status.HTTP_200_OK)

        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # вывод в консоль для отладки
            print("🚨 TripAPI internal error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripSummaryAPI(APIView):
    def get(self, request, vehicle_id):
        serializer = TripSummaryRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        dto = TripSummaryRequestDTO(
            vehicle_id=vehicle_id,
            start_time=request.query_params.get('start'),
            end_time=request.query_params.get('end')
        )

        try:
            result = TripService.get_trip_summary(dto)
            result_data = [{
                "start_time_local": item.start_time_local,
                "end_time_local": item.end_time_local,
                "duration": item.duration,
                "start_location": item.start_location,
                "start_address": item.start_address,
                "end_location": item.end_location,
                "end_address": item.end_address
            } for item in result]

            return Response(result_data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'cars/vehicle_info.html'
    context_object_name = 'vehicle'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.object

        dto = VehicleDetailDTO(
            vehicle_id=vehicle.id,
            start_time=self.request.GET.get('start'),
            end_time=self.request.GET.get('end')
        )

        try:
            context.update(VehicleDetailService.get_context(dto))
        except Exception as e:
            # В случае ошибки просто используем контекст по умолчанию
            context['start_value'] = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')
            context['end_value'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
            context['trip_list'] = []
            context['trip_data_json'] = '[]'

        return context


# Экспорт данных предприятия
def export_data(request):
    enterprise_id = request.GET.get('enterprise_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    file_format = request.GET.get('file_format', 'json')

    try:
        ent_dataset, veh_dataset, trip_dataset, file_format = ImportExportService.export_data(
            enterprise_id, start_str, end_str, file_format
        )
        response, filename = ImportExportService.handle_export_response(
            ent_dataset, veh_dataset, trip_dataset, file_format
        )

        if isinstance(response, HttpResponse):
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            response = FileResponse(response, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    except Exception as e:
        return HttpResponse(f"Ошибка при экспорте: {str(e)}", status=500)


# Импорт данных по предприятию
def import_data(request):
    if request.method == 'POST':
        file = request.FILES.get('file_import')
        if not file:
            return HttpResponse("Файл не выбран", status=400)

        try:
            fn = file.name.lower()
            if fn.endswith('.json'):
                ImportExportService.import_json(file)
            elif fn.endswith('.zip'):
                ImportExportService.import_csv_zip(file)
            else:
                return HttpResponse("Неподдерживаемый формат", status=400)

            return HttpResponse("Импорт данных завершён")
        except ValidationError as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse(f"Ошибка при импорте: {str(e)}", status=500)

    return HttpResponse("Используйте POST", status=405)

report_type = openapi.Parameter("report_type", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)
vehicle_id = openapi.Parameter("vehicle_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False)
driver_id = openapi.Parameter("driver_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False)
enterprise_id = openapi.Parameter("enterprise_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False)
start_date = openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False)
end_date = openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False)
period = openapi.Parameter("period", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description="day/week/month")

@swagger_auto_schema(
    method="get",
    operation_summary="Сформировать отчёт",
    manual_parameters=[report_type, vehicle_id, driver_id, enterprise_id, start_date, end_date, period],
    responses={
        status.HTTP_200_OK: openapi.Response(description="Отчёт (JSON)"),
        status.HTTP_400_BAD_REQUEST: openapi.Response(description="Ошибка в параметрах"),
    },
    tags=["Reports"],
)

@api_view(['GET'])
def report_api(request):
    dto = ReportRequestDTO(
        report_type=request.GET.get('report_type'),
        vehicle_id=request.GET.get('vehicle_id'),
        driver_id=request.GET.get('driver_id'),
        enterprise_id=request.GET.get('enterprise_id'),
        start_date=request.GET.get('start_date'),
        end_date=request.GET.get('end_date'),
        period=request.GET.get('period', 'day')
    )

    result = ReportService.generate_report(dto)

    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)


def reports_list(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            try:
                # Используем сервис для создания отчета
                report = ReportFormService.create_report(form.cleaned_data)
                messages.success(request, f"Отчёт '{report.name}' успешно создан.")
                return redirect('cars:reports_list')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Ошибка при создании отчёта: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ReportForm()

    reports = Report.objects.all().order_by('-created_at')
    context = {'form': form, 'reports': reports}
    return render(request, 'cars/reports_list.html', context)


def view_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return JsonResponse(report.result, safe=False)


def upload_trip(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        form = TripUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dto = TripUploadDTO(
                vehicle_id=vehicle_id,
                start_time=form.cleaned_data['start_time'],
                end_time=form.cleaned_data['end_time'],
                gpx_file=request.FILES['gpx_file'].read()
            )

            try:
                TripUploadService.upload_trip(dto)
                messages.success(request, "Поездка успешно добавлена!")
                return redirect('cars:vehicle_info', pk=vehicle.id)
            except ValidationError as e:
                form.add_error(None, str(e))
        # Обработка невалидной формы
        return render(request, 'cars/upload_trip.html', {'form': form, 'vehicle': vehicle})

    # GET запрос
    form = TripUploadForm()
    return render(request, 'cars/upload_trip.html', {'form': form, 'vehicle': vehicle})
    
@csrf_exempt
def test_view(request):
    return JsonResponse({"ok": True})
    
@csrf_exempt
def test_async_post(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid JSON"}, status=400)

        # Добавим немного тестовых данных
        fake_data = {
            "name": data.get("name", "Test Driver"),
            "license_number": data.get("license_number", "FAKE123"),
            "enterprise_id": data.get("enterprise_id", 1)
        }

        # Асинхронно отправляем задачу в Celery
        save_driver_data.delay(fake_data)

        return JsonResponse({"status": "accepted", "data": fake_data}, status=202)

    return JsonResponse({"error": "method not allowed"}, status=405)
