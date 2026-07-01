from django.core.management.base import BaseCommand
from apps.ged.models import Document


class Command(BaseCommand):
    help = 'Réindexe le texte extrait de tous les documents'

    def handle(self, *args, **options):
        qs = Document.objects.filter(file_type__in=['txt', 'pdf', 'docx'])
        total = qs.count()
        done = 0
        for doc in qs:
            try:
                doc.save(update_fields=['content_text'])
                done += 1
            except Exception as e:
                self.stderr.write(f'Erreur {doc.pk} ({doc.title}): {e}')
        self.stdout.write(f'{done}/{total} documents réindexés.')
