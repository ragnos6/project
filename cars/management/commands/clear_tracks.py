from django.core.management.base import BaseCommand
from django.conf import settings
import shutil, os

from cars.models import TrackPoint, Trip

class Command(BaseCommand):
    help = "Удалить все поездки, трек‑точки и связанные GPX‑файлы"

    def handle(self, *args, **kwargs):
        tp_deleted = TrackPoint.objects.all().delete()[0]
        trip_deleted = Trip.objects.all().delete()[0]
        self.stdout.write(f"TrackPoint удалено: {tp_deleted}")
        self.stdout.write(f"Trip удалено: {trip_deleted}")

        gpx_dir = os.path.join(settings.MEDIA_ROOT, 'gpx_tracks')
        if os.path.isdir(gpx_dir):
            shutil.rmtree(gpx_dir)
            self.stdout.write("Папка с GPX‑файлами очищена.")
        else:
            self.stdout.write("GPX‑директория отсутствует – пропущено.")

