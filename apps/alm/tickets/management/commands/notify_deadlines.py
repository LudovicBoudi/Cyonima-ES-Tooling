from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.alm.tickets.models import Ticket
from apps.notifications.utils import notify_ticket_deadline_approaching


class Command(BaseCommand):
    help = 'Notifie les utilisateurs des tickets dont l\'échéance approche (dans les 2 jours)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        deadline = today + timedelta(days=2)
        tickets = Ticket.objects.filter(
            due_date=deadline,
            status__in=['nouveau', 'assigne', 'en_cours'],
        ).select_related('assigned_to', 'project')
        count = 0
        for ticket in tickets:
            notify_ticket_deadline_approaching(ticket)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} notifications d\'échéance envoyées'))
