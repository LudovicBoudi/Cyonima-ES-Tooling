from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import Notification, NotificationSetting


class Command(BaseCommand):
    help = 'Envoie le résumé quotidien des notifications aux utilisateurs abonnés'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        users_with_digest = NotificationSetting.objects.filter(digest_daily=True).select_related('user')
        count = 0
        for ns in users_with_digest:
            user = ns.user
            if not user.email:
                continue
            notifs = Notification.objects.filter(
                user=user, created_at__date__gte=yesterday, is_read=False
            )[:20]
            if not notifs:
                continue
            lines = [f"• {n.title}: {n.message}" for n in notifs]
            body = f"Bonjour {user.username},\n\nVoici le résumé des {len(notifs)} notification(s) non lue(s) :\n\n" + "\n\n".join(lines) + f"\n\n— {settings.SITE_URL}"
            send_mail(
                subject=f"[Cyonima] Résumé quotidien du {today.strftime('%d/%m/%Y')}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            self.stdout.write(f'Digest envoyé à {user.username} ({len(notifs)} notifs)')
            count += 1
        self.stdout.write(f'{count} digests envoyés.')
