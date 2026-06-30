from django.db import models
from django.contrib.auth.models import User
from apps.alm.projects.models import Project


class Requirement(models.Model):
    CATEGORY_CHOICES = [
        ('folder', 'Dossier'),
        ('metier', 'Métier'),
        ('infrastructure', 'Infrastructure'),
        ('logiciel', 'Logiciel'),
        ('securite', 'Sécurité'),
        ('reseau', 'Réseau'),
        ('administration', 'Administration'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    number = models.IntegerField(editable=False, verbose_name='Numéro')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Catégorie')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(max_length=4000, blank=True, verbose_name='Description')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exigence'
        verbose_name_plural = 'Exigences'
        unique_together = [('project', 'number')]
        ordering = ['number']

    def __str__(self):
        return f"{self.get_formatted_number()} - {self.name}"

    def get_formatted_number(self):
        if self.category == 'folder':
            return f"D-{self.number:04d}"
        return f"{self.number:04d}"

    def get_children_tree(self):
        result = []
        for child in self.children.all():
            result.append(child)
            result.extend(child.get_children_tree())
        return result

    def save(self, *args, **kwargs):
        if not self.pk:
            last = Requirement.objects.filter(project=self.project).order_by('-number').first()
            self.number = (last.number + 1) if last else 1
        super().save(*args, **kwargs)


class RequirementAttachment(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='requirements/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'

    def __str__(self):
        return self.filename
