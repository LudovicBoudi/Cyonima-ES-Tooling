from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.conf import settings
import zipfile
import io
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Crée une sauvegarde complète (données + media)'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'cyonima_backup_{timestamp}.zip'
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('version.txt', f'Sauvegarde Cyonima-ES-Tools - {datetime.now().isoformat()}\n')

            for model in apps.get_models():
                app_label = model._meta.app_label
                model_name = model.__name__
                try:
                    data = serializers.serialize('json', model.objects.all())
                    if data != '[]':
                        zf.writestr(f'data/{app_label}.{model_name}.json', data)
                except Exception:
                    pass

            media_root = settings.MEDIA_ROOT
            if os.path.isdir(media_root):
                for root, dirs, files in os.walk(media_root):
                    for f in files:
                        path = os.path.join(root, f)
                        arcname = os.path.relpath(path, media_root)
                        zf.write(path, f'media/{arcname}')

            zf.writestr('settings.txt', f"DEBUG={settings.DEBUG}\nALLOWED_HOSTS={','.join(settings.ALLOWED_HOSTS)}\nLANGUAGE={settings.LANGUAGE_CODE}\nTIME_ZONE={settings.TIME_ZONE}\n")

        output_path = os.path.join(settings.BASE_DIR, filename)
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())

        self.stdout.write(self.style.SUCCESS(f'Sauvegarde créée : {output_path} ({len(buffer.getvalue()) / 1024:.1f} KB)'))
