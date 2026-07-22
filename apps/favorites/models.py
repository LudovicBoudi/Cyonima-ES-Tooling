from django.db import models
from django.contrib.auth.models import User


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField('Type', max_length=100)
    object_id = models.PositiveIntegerField('ID')
    label = models.CharField('Libellé', max_length=300)
    module = models.CharField('Module', max_length=50)
    url = models.CharField('URL', max_length=500)
    created_at = models.DateTimeField('Ajouté le', auto_now_add=True)

    class Meta:
        verbose_name = 'Favori'
        verbose_name_plural = 'Favoris'
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.label} ({self.module})'
