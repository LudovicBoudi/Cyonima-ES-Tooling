from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class NotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notif_settings')
    email_dat_creation = models.BooleanField(default=True, verbose_name='Email création DAT')
    email_ticket_change = models.BooleanField(default=True, verbose_name='Email changement ticket')
    email_report_ready = models.BooleanField(default=True, verbose_name='Email rapport disponible')
    email_erp_notification = models.BooleanField(default=True, verbose_name='Email notification ERP')
    digest_daily = models.BooleanField(default=False, verbose_name='Résumé quotidien')

    class Meta:
        verbose_name = 'Préférence notification'
        verbose_name_plural = 'Préférences notifications'


class Notification(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('in_app', 'In-app'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='in_app')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
