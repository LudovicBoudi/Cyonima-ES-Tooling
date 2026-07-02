from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from .models import Notification, NotificationSetting


def create_notification(user, title, message, link='', notification_type='in_app'):
    if not user:
        return
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
    if notification_type == 'email' or True:
        try:
            settings_obj = NotificationSetting.objects.filter(user=user).first()
            email_enabled = settings_obj and settings_obj.email_ticket_change
            if email_enabled and user.email:
                full_link = f"{settings.SITE_URL}{link}" if link else ''
                body = f"{message}\n\n{full_link}".strip()
                send_mail(
                    subject=f"[{settings.SITE_URL}] {title}",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except Exception:
            pass


def notify_ticket_assigned(ticket, assigned_to, assigned_by):
    if not assigned_to or assigned_to == assigned_by:
        return
    create_notification(
        assigned_to,
        f"Nouveau ticket : {ticket.get_formatted_number()}",
        f"Vous avez été assigné au ticket {ticket.get_formatted_number()} - {ticket.title}",
        link=f"/projects/{ticket.project_id}/tickets/{ticket.id}/",
    )


def notify_ticket_status_changed(ticket, old_status, new_status, changed_by):
    if not ticket.assigned_to or ticket.assigned_to == changed_by:
        return
    create_notification(
        ticket.assigned_to,
        f"Statut mis à jour : {ticket.get_formatted_number()}",
        f"Le ticket {ticket.get_formatted_number()} - {ticket.title} est passé de {old_status} à {new_status}",
        link=f"/projects/{ticket.project_id}/tickets/{ticket.id}/",
    )


def notify_ticket_deadline_approaching(ticket):
    if not ticket.assigned_to:
        return
    create_notification(
        ticket.assigned_to,
        f"Échéance approchante : {ticket.get_formatted_number()}",
        f"Le ticket {ticket.get_formatted_number()} - {ticket.title} arrive à échéance le {ticket.due_date}",
        link=f"/projects/{ticket.project_id}/tickets/{ticket.id}/",
    )
