from .models import SiteConfig
from apps.notifications.models import Notification


def site_config(request):
    config = SiteConfig.objects.first()
    ctx = {'site_config': config or {'site_name': 'Cyonima-ES-Tools', 'logo': None}}
    if request.user.is_authenticated:
        ctx['unread_notifications_count'] = Notification.objects.filter(user=request.user, is_read=False).count()
    return ctx
