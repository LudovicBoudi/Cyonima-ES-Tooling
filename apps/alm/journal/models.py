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
        verbose_name = "Compte rendu d'activité"
        verbose_name_plural = "Comptes rendus d'activité"
        ordering = ['-report_date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.report_date}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('status_change', 'Changement de statut'),
        ('assign', 'Assignation'),
        ('comment', 'Commentaire'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='alm_audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name='Action')
    entity_type = models.CharField(max_length=50, verbose_name='Type d\'entité')
    entity_id = models.IntegerField(null=True, blank=True, verbose_name='ID entité')
    summary = models.CharField(max_length=255, verbose_name='Résumé')
    details = models.TextField(blank=True, verbose_name='Détails')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Journal de modification'
        verbose_name_plural = 'Journal des modifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at|date:'Y-m-d H:i'} - {self.user} - {self.action} - {self.summary}"
