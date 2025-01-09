import time
import math
import random
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from cars.models import Vehicle, TrackPoint, Trip
import openrouteservice

class Command(BaseCommand):
    help = "Создание трека автомобиля"

    def add_arguments(self, parser):
        parser.add_argument('vehicle_id', type=int, help="ID автомобиля")
        parser.add_argument('--length', type=float, default=10.0, help="Длина маршрута")
        parser.add_argument('--step', type=float, default=0.1, help="Шаг точек")
        parser.add_argument('--area', type=str, default="37.6173,55.7558", help="Центр окружности")
        parser.add_argument('--radius', type=int, default=5, help="Радиус от центра в километрах")

    def handle(self, *args, **options):
        vehicle_id = options['vehicle_id']
        track_length = options['length']
        step = options['step']
        area = [float(x) for x in options['area'].split(',')]
        radius = options['radius'] * 1000  # Convert to meters
        api_key = '5b3ce3597851110001cf6248c0e44487163c470cb6c35dec635ce056'

        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            self.stderr.write(f"Автомобиль с номером {vehicle_id} не существует")
            return

        client = openrouteservice.Client(key=api_key)

        # Генерация конечной точки на окружности заданного радиуса
        angle = random.uniform(0, 2 * math.pi)  # Случайный угол в радианах
        delta_lat = (radius / 111320) * math.sin(angle)  # Смещение по широте
        delta_lon = (radius / (111320 * math.cos(math.radians(area[1])))) * math.cos(angle)  # Смещение по долготе

        end_point = [area[0] + delta_lon, area[1] + delta_lat]

        try:
            route = client.directions(
                coordinates=[area, end_point],
                profile='driving-car',
                format='geojson'
            )
        except Exception as e:
            self.stderr.write(f"Failed to fetch route: {e}")
            return

        # Получение координат маршрута
        coordinates = route['features'][0]['geometry']['coordinates']

        # Генерация точек и запись их в базу с учетом длины маршрута и шага
        total_distance = 0
        accumulated_distance = 0

        self.stdout.write(f"Начало генерации точек для автомобиля {vehicle_id}")
        start_time = now()

        for i in range(1, len(coordinates)):
            lon1, lat1 = coordinates[i - 1]
            lon2, lat2 = coordinates[i]

            # Рассчитываем расстояние между точками
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            total_distance += distance
            accumulated_distance += distance

            # Добавляем точку, если накопленное расстояние превышает шаг
            if accumulated_distance >= step:
                TrackPoint.objects.create(
                    vehicle=vehicle,
                    location=f"POINT({lon2} {lat2})",
                    timestamp=now()
                )
                self.stdout.write(f"Добавлена точка: ({lon2}, {lat2})")
                accumulated_distance = 0
                time.sleep(10)  # Эмуляция реального времени

            if total_distance >= track_length:
                break

        end_time = now()
        
        Trip.objects.create(
            vehicle=vehicle,
            start_time=start_time,
            end_time=end_time
        )
        
        self.stdout.write("Генерация точек завершена.")
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


