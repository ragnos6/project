from django.utils.timezone import localtime
import zoneinfo

def convert_to_enterprise_timezone(vehicle):
    tz = zoneinfo.ZoneInfo(vehicle.enterprise.timezone)
    return localtime(vehicle.purchase_date, tz)
