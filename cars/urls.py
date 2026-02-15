from django.urls import path, include
from .views import EnterpriseViewSet, VehicleViewSet, DriverViewSet, CustomAuthToken, ManagerLoginView, VehicleManageView, VehicleEditView, VehicleDeleteView, EnterpriseListView, TrackPointView, TripAPI, TripSummaryAPI, VehicleDetailView, export_data, import_data, report_api, reports_list, view_report, upload_trip, test_view, test_async_post
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


router = DefaultRouter()
router.register(r'enterprises', EnterpriseViewSet, basename='enterprise')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'drivers', DriverViewSet, basename='driver')

schema_url_patterns = [
    path("api/", include(router.urls)),
    path("api/api-token-auth/", CustomAuthToken.as_view()),
    path("api/vehicles/<int:vehicle_id>/trips/", TripAPI.as_view()),
    path("api/report-api/", report_api),
]

schema_view = get_schema_view(
    openapi.Info(
        title="Cars API",
        default_version="v1",
        description="API: vehicles, trips, auth, reports",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=schema_url_patterns,
)

app_name='cars'
urlpatterns = [
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path('', include(router.urls)),
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('login/', ManagerLoginView.as_view(), name='login'),
    path('enterprises_list/', EnterpriseListView.as_view(), name='enterprises_list'),
    path('export-data/', export_data, name='export_data'),
    path('import-data/', import_data, name='import_data'),
    path('enterprises/<int:enterprise_id>/vehicles/', VehicleManageView.as_view(), name='manage_vehicles'),
    path('vehicles/<int:pk>/edit/', VehicleEditView.as_view(), name='edit_vehicle'),
    path('vehicles/<int:pk>/delete/', VehicleDeleteView.as_view(), name='delete_vehicle'),
    path('vehicles/<int:pk>/info/', VehicleDetailView.as_view(), name='vehicle_info'),
    path('vehicles/<int:vehicle_id>/track/', TrackPointView.as_view(), name='vehicle_track'),
    path('vehicles/<int:vehicle_id>/trips/', TripAPI.as_view(), name='vehicle_trips'),
    path('vehicles/<int:vehicle_id>/trip_summary/', TripSummaryAPI.as_view(), name='trip_summary'),
    path('vehicles/<int:vehicle_id>/upload_trip/', upload_trip, name='upload_trip'),
    path('reports/', reports_list, name='reports_list'),
    path('report-api/', report_api, name='report_api'),
    path('reports/<int:report_id>/', view_report, name='view_report'),
    path("test/", test_view),
    path("test_async/", test_async_post, name="test_async_post"),


]
