from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.erp.models import Invoice, Reminder
from apps.notifications.utils import create_notification


class Command(BaseCommand):
    help = 'Crée automatiquement des relances pour les factures impayées depuis plus de 30 jours'

    def handle(self, *args, **options):
        threshold = timezone.now().date() - timedelta(days=30)
        overdue_invoices = Invoice.objects.filter(
            status__in=['emise', 'impayee'],
            due_date__lte=threshold,
        ).select_related('company', 'contact')

        created_count = 0
        for invoice in overdue_invoices:
            existing_reminders = Reminder.objects.filter(invoice=invoice).count()
            if existing_reminders == 0:
                Reminder.objects.create(
                    invoice=invoice,
                    level=1,
                    amount_due=invoice.remaining(),
                    created_by=None,
                )
                created_count += 1
                if invoice.contact and hasattr(invoice.contact, 'portal_user'):
                    create_notification(
                        invoice.contact.portal_user.user,
                        title=f'Relance : {invoice.number}',
                        message=f'Votre facture {invoice.number} est en retard de paiement.',
                        link=f'/portail/factures/{invoice.pk}/',
                    )
                self.stdout.write(self.style.WARNING(
                    f'Relance niveau 1 créée pour {invoice.number} '
                    f'({invoice.company}) — reste : {invoice.remaining()} EUR'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'{created_count} relance(s) créée(s) sur {overdue_invoices.count()} facture(s) en retard.'
        ))
