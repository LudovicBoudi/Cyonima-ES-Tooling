from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.ged.models import Document
from apps.notifications.utils import create_notification


class Command(BaseCommand):
    help = 'Vérifie les documents arrivant à expiration et envoie des notifications'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        soon = today + timezone.timedelta(days=30)
        docs = Document.objects.filter(
            expiry_date__isnull=False, expiry_date__lte=soon,
            deleted_at__isnull=True
        )
        for doc in docs:
            if doc.created_by:
                days = (doc.expiry_date - today).days
                if days <= 0:
                    msg = f'⚠ Le document "{doc.title}" a expiré le {doc.expiry_date}.'
                else:
                    msg = f'📅 Le document "{doc.title}" expire dans {days} jour(s) (le {doc.expiry_date}).'
                create_notification(doc.created_by, 'Expiration document', msg, link=f'/ged/{doc.pk}/')
                self.stdout.write(f'Notif: {doc.title} ({days} jours)')
        self.stdout.write(f'{docs.count()} document(s) vérifié(s).')
