from django.urls import path, include
from .views import EnterpriseViewSet, VehicleViewSet, DriverViewSet, test, CustomAuthToken, ManagerLoginView, VehicleManageView, VehicleEditView, VehicleDeleteView, EnterpriseListView, TrackPointView, TripAPI, TripSummaryAPI, VehicleDetailView, export_data, import_data, report_api, reports_list, view_report
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'enterprises', EnterpriseViewSet, basename='enterprise')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'drivers', DriverViewSet, basename='driver')

app_name='cars'
urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('test', test, name='test'),
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
    path('reports/', reports_list, name='reports_list'),
    path('report-api/', report_api, name='report_api'),
    path('reports/<int:report_id>/', view_report, name='view_report'),
]

# Token:43f9553733f75df08073d9acad8fdc34b6735497
