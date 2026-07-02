from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ComArticle(models.Model):
    year = models.IntegerField(editable=False)
    sequence_number = models.IntegerField(editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(verbose_name='Contenu')
    image = models.ImageField(upload_to='blog/images/', blank=True, null=True, verbose_name='Image à la une')
    status = models.CharField(max_length=20, choices=[('brouillon', 'Brouillon'), ('publie', 'Publié')], default='publie', verbose_name='Statut')
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags', help_text='Séparés par des virgules')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article communication'
        verbose_name_plural = 'Articles communication'
        unique_together = [('year', 'sequence_number')]
        ordering = ['-year', '-sequence_number']

    def __str__(self):
        return self.display_id()

    def display_id(self):
        return f"COM-{self.year}-{self.sequence_number:04d}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.year = timezone.now().year
            last = ComArticle.objects.filter(year=self.year).order_by('-sequence_number').first()
            self.sequence_number = (last.sequence_number + 1) if last else 1
        super().save(*args, **kwargs)


class ComArticleAttachment(models.Model):
    article = models.ForeignKey(ComArticle, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='blog/com/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
