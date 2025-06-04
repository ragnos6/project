import os
import random
import datetime
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.conf import settings
from django.db.models import Max

import warnings
import osmnx as ox
import networkx as nx

from cars.models import Vehicle, TrackPoint, Trip

# ------------------------------------------------- Параметры и константы
GRAPH_DIR  = os.path.join(settings.BASE_DIR, "data")
GRAPH_PATH = os.path.join(GRAPH_DIR, "moscow_district.graphml")

DEFAULT_SPEED = {
    'motorway': 100, 'trunk': 80, 'primary': 60,
    'secondary': 50, 'tertiary': 40,
    'residential': 30, 'service': 20,
}

# ------------------------------------------------- Вспомогательные функции

def normalize_osm_tag(value):
    """Возвращает первый элемент для списков/кортежей OSM‑тегов,
    либо исходное значение, если это не коллекция."""
    if isinstance(value, (list, tuple)):
        return value[0]
    return value

def parse_speed(maxspd, hw_type):
    """Преобразует тег maxspeed в число км/ч, используя резервный словарь
    при невозможности разобрать значение."""
    maxspd = normalize_osm_tag(maxspd)
    if maxspd:
        try:
            return float(str(maxspd).split(';')[0])
        except (ValueError, TypeError):
            pass
    return DEFAULT_SPEED.get(hw_type, 30)


def get_safe_start(vehicle, duration, now):
    """Подбирает начало поездки так, чтобы она не пересекалась
    с существующими поездками данного автомобиля."""
    latest_end = (
        Trip.objects.filter(vehicle=vehicle)
        .aggregate(Max('end_time'))['end_time__max']
    )
    if latest_end is None:
        start = now - timedelta(days=random.randint(0, 30))
    else:
        start = latest_end + timedelta(minutes=random.randint(5, 60))
    return start, start + duration

# ------------------------------------------------- Основная команда
class Command(BaseCommand):
    """Генератор реалистичных поездок без перекрытий во времени."""

    def add_arguments(self, parser):
        parser.add_argument('--num-trips', type=int, default=100,
                            help='Сколько поездок создать')
        parser.add_argument('--points-per-trip', type=int, default=50,
                            help='Максимальное число точек на одну поездку')
        parser.add_argument('--district', type=str,
                            default="Tverskoy District, Moscow, Russia",
                            help='Название района для генерации (OSM place)')
        parser.add_argument('--with-gpx', action='store_true',
                            help='Сохранять GPX‑файлы')

    # --------------------------------------------- Загрузка графа OSM
    def load_graph(self, place_name):
        """Загружает или кэширует граф OSM **в исходной географической CRS
        (EPSG:4326)**, чтобы сохранять широту/долготу без дополнительного
        преобразования. Атрибуты `length` уже заданы в метрах самим OSMnx,
        поэтому проецирование не требуется для расчёта времени движения."""

        warnings.filterwarnings(
            "ignore",
            message="This area is .* your configured Overpass max query area size"
        )
        os.makedirs(GRAPH_DIR, exist_ok=True)

        if os.path.exists(GRAPH_PATH):
            self.stdout.write("Загрузка сохранённого графа района…")
            G = ox.load_graphml(GRAPH_PATH)
        else:
            self.stdout.write("Скачивание и сохранение графа района из OSM…")
            G = ox.graph_from_place(place_name, network_type='drive')
            ox.save_graphml(G, GRAPH_PATH)

        # Оставляем крупнейшую связную компоненту
        Gu = G.to_undirected()
        largest_cc = max(nx.connected_components(Gu), key=len)
        return G.subgraph(largest_cc).copy()

    # --------------------------------------------- Генерация маршрута
    def sample_route(self, G):
        """Возвращает список Point‑координат и массив интервалов времени
        между ними, гарантируя существование пути."""
        nodes = list(G.nodes)
        for _ in range(100):
            u, v = random.sample(nodes, 2)
            try:
                path = nx.shortest_path(G.to_undirected(), u, v, weight='length')
                break
            except nx.NetworkXNoPath:
                continue
        else:
            raise RuntimeError("Не удалось найти связанный путь после 100 попыток.")

        pts, seg_dt = [], []
        for a, b in zip(path, path[1:]):
            # Данные ребра независимо от направления
            if G.has_edge(a, b):
                edge_data = G.get_edge_data(a, b)[0]
            else:
                edge_data = G.get_edge_data(b, a)[0]

            geom = edge_data.get('geometry')
            coords = list(geom.coords) if geom else [
                (G.nodes[a]['x'], G.nodes[a]['y']),
                (G.nodes[b]['x'], G.nodes[b]['y'])
            ]
            length = edge_data.get('length', 0)

            hw_type_raw = edge_data.get('highway', 'residential')
            hw_type = normalize_osm_tag(hw_type_raw)

            speed = parse_speed(edge_data.get('maxspeed'), hw_type)
            segment_time = length / (speed * 1000/3600)  # секунд
            dt = segment_time / max(1, len(coords))

            for x, y in coords:
                pts.append(Point(x, y, srid=4326))
                seg_dt.append(dt)

        return pts, seg_dt

    # --------------------------------------------- Основной цикл
    def handle(self, *args, **opts):
        num_trips    = opts['num_trips']
        pts_per_trip = opts['points_per_trip']
        district     = opts['district']
        save_gpx     = opts['with_gpx']

        vehicles = list(Vehicle.objects.all())
        if not vehicles:
            self.stderr.write("Ошибка: в базе нет ни одного Vehicle.")
            return

        G = self.load_graph(district)
        now = timezone.now()
        created = 0

        for _ in range(num_trips):
            vehicle = random.choice(vehicles)
            pts, times = self.sample_route(G)

            if len(pts) > pts_per_trip:
                idxs = sorted(random.sample(range(len(pts)), pts_per_trip))
                pts   = [pts[i]   for i in idxs]
                times = [times[i] for i in idxs]

            zero_ts = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
            stamps = [zero_ts]
            for dt_s in times[:-1]:
                stamps.append(stamps[-1] + timedelta(seconds=dt_s))
            duration = stamps[-1] - stamps[0]

            start_time, end_time = get_safe_start(vehicle, duration, now)
            offset = start_time - zero_ts
            stamps = [ts + offset for ts in stamps]

            trip = Trip.objects.create(vehicle=vehicle,
                                       start_time=start_time,
                                       end_time=end_time)

            TrackPoint.objects.bulk_create([
                TrackPoint(vehicle=vehicle, timestamp=ts, location=pt)
                for pt, ts in zip(pts, stamps)
            ])

            if save_gpx:
                import gpxpy, gpxpy.gpx
                gpx = gpxpy.gpx.GPX()
                trk = gpxpy.gpx.GPXTrack()
                seg = gpxpy.gpx.GPXTrackSegment()
                for pt, ts in zip(pts, stamps):
                    seg.points.append(gpxpy.gpx.GPXTrackPoint(pt.y, pt.x, time=ts))
                trk.segments.append(seg)
                gpx.tracks.append(trk)

                fn = f"{vehicle.pk}_{trip.pk}.gpx"
                out = os.path.join(settings.MEDIA_ROOT, "gpx_tracks", fn)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    f.write(gpx.to_xml())

                trip.gpx_file.name = f"gpx_tracks/{fn}"
                trip.save(update_fields=['gpx_file'])

            created += 1
            if created % 10 == 0:
                self.stdout.write(f"Создано поездок: {created}/{num_trips}")

        self.stdout.write(
            f"Генерация завершена. Всего создано поездок: {created} в районе «{district}»."
        )

