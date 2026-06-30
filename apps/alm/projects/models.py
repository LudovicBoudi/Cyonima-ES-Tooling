from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Créé par')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def user_is_member(self, user):
        return self.members.filter(user=user).exists()

    def user_can_access(self, user):
        if hasattr(user, 'profile') and user.profile.is_admin():
            return True
        return self.user_is_member(user)


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('chef_projet', 'Chef de projet'),
        ('developpeur', 'Développeur'),
        ('testeur', 'Testeur'),
        ('integrateur', 'Intégrateur'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='Rôle')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membre du projet'
        verbose_name_plural = 'Membres du projet'
        unique_together = [('project', 'user')]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
