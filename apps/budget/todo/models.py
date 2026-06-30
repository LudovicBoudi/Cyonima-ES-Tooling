from django.db import models
from django.utils import timezone


class TodoItem(models.Model):
    STATUS_CHOICES = [
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('done', 'Réalisé'),
    ]
    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    deadline = models.DateField(verbose_name='Date limite')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Statut')
    order = models.IntegerField(default=0, verbose_name='Ordre')

    class Meta:
        verbose_name = 'Tâche'
        verbose_name_plural = 'Tâches'
        ordering = ['order', 'deadline']

    def __str__(self):
        return self.title

    def color_class(self):
        if self.status == 'done':
            return 'done'
        today = timezone.now().date()
        delta = (self.deadline - today).days
        if delta < 0:
            return 'overdue'
        if delta == 0:
            return 'critical'
        if delta <= 7:
            return 'warning'
        return 'safe'
