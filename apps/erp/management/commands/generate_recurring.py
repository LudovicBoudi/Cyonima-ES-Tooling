from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from calendar import monthrange
from apps.erp.models import RecurringInvoice, Invoice


class Command(BaseCommand):
    help = 'Génère les factures récurrentes arrivées à échéance'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        due = RecurringInvoice.objects.filter(is_active=True, next_date__lte=today)
        count = 0
        for r in due:
            inv = Invoice.objects.create(
                company=r.company,
                lines=r.lines,
                created_by=r.created_by,
                status='emise',
            )
            if r.frequency == 'monthly':
                month = r.next_date.month + 1
                year = r.next_date.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                day = min(r.next_date.day, monthrange(year, month)[1])
                r.next_date = r.next_date.replace(year=year, month=month, day=day)
            elif r.frequency == 'quarterly':
                month = r.next_date.month + 3
                year = r.next_date.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                day = min(r.next_date.day, monthrange(year, month)[1])
                r.next_date = r.next_date.replace(year=year, month=month, day=day)
            else:
                r.next_date = r.next_date.replace(year=r.next_date.year + 1)
            r.save()
            self.stdout.write(f'Facture {inv.number} créée pour {r.company} ({r.title})')
            count += 1
        self.stdout.write(f'{count} facture(s) générée(s).')
