from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from apps.notifications.models import Notification, NotificationSetting
from .models import ErpAuditLog


def log_audit(request, model_name, object_id, object_repr, action, details=''):
    ErpAuditLog.objects.create(
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR'),
    )


def notify_user(user, title, message, link=''):
    Notification.objects.create(
        user=user,
        notification_type='in_app',
        title=title,
        message=message,
        link=link,
    )
    try:
        if user.notif_settings.email_erp_notification and user.email:
            send_mail(
                subject=f'[Cyonima ERP] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@cyonima.com',
                recipient_list=[user.email],
                fail_silently=True,
            )
    except NotificationSetting.DoesNotExist:
        pass


def notify_admins(title, message, link=''):
    for user in User.objects.filter(is_staff=True):
        notify_user(user, title, message, link)
