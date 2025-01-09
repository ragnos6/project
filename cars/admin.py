from django.contrib import admin
from cars.models import Vehicle, VehicleDocumentation, Model, Enterprise, Driver, VehicleDriver, Manager, TrackPoint
from django.contrib.gis import admin as geoadmin
from leaflet.admin import LeafletGeoAdmin

class CarsAssigment(admin.TabularInline):
    model = VehicleDriver
    extra = 1
    verbose_name = 'Водитель авто'
    verbose_name_plural = 'Водители авто'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'documentation', 'year_of_production', 'enterprise', 'cost', 'mileage', 'color', 'active_driver')
    inlines = [CarsAssigment]
    
    def view_track_map(self, obj):
        url = reverse('admin:view_track_map', args=[obj.id])
        return format_html(f'<a href="{url}" target="_blank">View Track Map</a>')

    view_track_map.short_description = "Track Map"
@admin.register(VehicleDocumentation)
class VehicleDocumentationAdmin(admin.ModelAdmin):
    list_display = ('vin_number', 'pts_number', 'reg_number', 'registration_date', 'owner_name')
    
    
@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_type', 'power_capacity','fuel_capacity', 'payload_capacity', 'seating_capacity')
  
@admin.register(Enterprise)  
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'timezone',)
    list_filter = ('timezone',)
    search_fields = ('name',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'salary')
    
@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_enterprises")
    filter_horizontal = ("enterprises",)

    def get_enterprises(self, obj):
        return ", ".join([enterprise.name for enterprise in obj.enterprises.all()])
    get_enterprises.short_description = "Предприятия"

@admin.register(TrackPoint)
class TrackPointAdmin(LeafletGeoAdmin):
    list_display = ('vehicle', 'timestamp', 'location')
    list_filter = ('vehicle', 'timestamp')
