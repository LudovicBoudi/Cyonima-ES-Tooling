from django.db import models
from django.contrib.auth.models import User
from apps.alm.projects.models import Project


class ActivityReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activity_reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_date = models.DateField(verbose_name='Date du rapport')
    content = models.TextField(verbose_name='Contenu')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compte rendu d\'activité'
        verbose_name_plural = 'Comptes rendus d\'activité'
        ordering = ['-report_date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.report_date}"
