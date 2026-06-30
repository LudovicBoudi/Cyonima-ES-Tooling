from django.db import models


class SiteConfig(models.Model):
    site_name = models.CharField(max_length=100, default='Cyonima-ES-Tools')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, help_text='Recommandé 120x40 px, PNG/SVG')

    class Meta:
        verbose_name = 'Configuration du site'
        verbose_name_plural = 'Configuration du site'

    def __str__(self):
        return self.site_name
