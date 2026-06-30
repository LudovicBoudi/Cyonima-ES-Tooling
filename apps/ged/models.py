from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


def next_registration_number():
    year = timezone.now().year
    prefix = f'DOC-{year}-'
    last = Document.objects.filter(registration_number__startswith=prefix).order_by('registration_number').last()
    if last:
        seq = int(last.registration_number.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:05d}'


class DocumentCategory(models.Model):
    name = models.CharField('Nom', max_length=100)
    color = models.CharField('Couleur', max_length=7, default='#1a3a6b', help_text='Hex (#1a3a6b)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']

    def __str__(self):
        return self.name


def document_upload_path(instance, filename):
    return f'ged/{instance.category.name if instance.category else "divers"}/{filename}'


class Document(models.Model):
    registration_number = models.CharField('N° enregistrement', max_length=20, unique=True, editable=False, null=True)
    title = models.CharField('Titre', max_length=255)
    file = models.FileField('Fichier', upload_to=document_upload_path)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents', verbose_name='Catégorie')
    description = models.TextField('Description', blank=True)
    version = models.CharField('Version', max_length=20, default='1.0')
    tags = models.CharField('Tags', max_length=500, blank=True, help_text='Séparés par des virgules')
    file_size = models.BigIntegerField('Taille (octets)', editable=False, default=0)
    file_type = models.CharField('Type', max_length=100, editable=False, blank=True)
    download_count = models.PositiveIntegerField('Téléchargements', default=0, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = next_registration_number()
        if self.file:
            self.file_size = self.file.size
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lower().lstrip('.') if ext else 'inconnu'
        super().save(*args, **kwargs)

    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

    def size_display(self):
        s = self.file_size
        if s >= 1024 * 1024:
            return f'{s / (1024 * 1024):.1f} Mo'
        elif s >= 1024:
            return f'{s / 1024:.1f} Ko'
        return f'{s} o'

    def __str__(self):
        return f'{self.title} (v{self.version})'
