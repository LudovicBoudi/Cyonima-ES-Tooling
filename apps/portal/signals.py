from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.erp.models import Quotation, Invoice, CreditNote
from apps.notifications.utils import create_notification


def _notify_portal_user(contact, title, message, link):
    try:
        portal_user = contact.portal_user
        if portal_user.is_active:
            create_notification(
                portal_user.user,
                title=title,
                message=message,
                link=link,
            )
    except Exception:
        pass


@receiver(post_save, sender=Quotation)
def notify_portal_quotation(sender, instance, created, **kwargs):
    if created and instance.contact:
        _notify_portal_user(
            instance.contact,
            title=f'Nouveau devis : {instance.number}',
            message=f'Un nouveau devis {instance.number} a été créé.',
            link=f'/portail/devis/{instance.pk}/',
        )


@receiver(post_save, sender=Invoice)
def notify_portal_invoice(sender, instance, created, **kwargs):
    if created and instance.contact:
        _notify_portal_user(
            instance.contact,
            title=f'Nouvelle facture : {instance.number}',
            message=f'Une nouvelle facture {instance.number} a été émise.',
            link=f'/portail/factures/{instance.pk}/',
        )


@receiver(post_save, sender=CreditNote)
def notify_portal_creditnote(sender, instance, created, **kwargs):
    if created and instance.invoice and instance.invoice.contact:
        _notify_portal_user(
            instance.invoice.contact,
            title=f'Nouvel avoir : {instance.number}',
            message=f'Un nouvel avoir {instance.number} a été émis.',
            link=f'/portail/avoirs/{instance.pk}/',
        )
