from django.db import models
from django.contrib.auth.models import User


class PageView(models.Model):
    url = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Visite'
        verbose_name_plural = 'Visites'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['url']),
        ]

    def __str__(self):
        return f'{self.url} — {self.timestamp.strftime("%d/%m/%Y %H:%M")}'
