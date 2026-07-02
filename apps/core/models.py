from django.db import models


class SiteConfig(models.Model):
    site_name = models.CharField(max_length=100, default='Cyonima-ES-Tools')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, help_text='Recommandé 120x40 px, PNG/SVG')
    https_enabled = models.BooleanField(default=False, verbose_name='HTTPS activé')
    hsts_seconds = models.PositiveIntegerField(default=31536000, verbose_name='Durée HSTS (secondes)', help_text='0 = désactivé. Défaut : 31536000 (1 an)')
    ssl_certificate = models.FileField(upload_to='ssl/', blank=True, null=True, verbose_name='Certificat SSL (.crt/.pem)')
    ssl_private_key = models.FileField(upload_to='ssl/', blank=True, null=True, verbose_name='Clé privée (.key)')

    class Meta:
        verbose_name = 'Configuration du site'
        verbose_name_plural = 'Configuration du site'

    def __str__(self):
        return self.site_name

    def cert_path(self):
        return self.ssl_certificate.path if self.ssl_certificate else None

    def key_path(self):
        return self.ssl_private_key.path if self.ssl_private_key else None
