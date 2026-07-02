from django.db import models
from apps.alm.projects.models import Project


class Repository(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='repositories')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    url = models.CharField(max_length=500, blank=True, verbose_name='URL distante')
    local_path = models.CharField(max_length=500, blank=True, verbose_name='Chemin local')
    branch = models.CharField(max_length=100, default='main', verbose_name='Branche par défaut')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dépôt'
        verbose_name_plural = 'Dépôts'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.project.name})"

    def repo_path(self):
        return self.local_path or ''

    def is_valid(self):
        from . import git_utils
        return git_utils.is_git_repo(self.repo_path())
