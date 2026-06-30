from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SecurityArticle(models.Model):
    year = models.IntegerField(editable=False)
    sequence_number = models.IntegerField(editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=10000)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article sécurité'
        verbose_name_plural = 'Articles sécurité'
        unique_together = [('year', 'sequence_number')]
        ordering = ['-year', '-sequence_number']

    def __str__(self):
        return self.display_id()

    def display_id(self):
        return f"Secu-{self.year}-{self.sequence_number:04d}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.year = timezone.now().year
            last = SecurityArticle.objects.filter(year=self.year).order_by('-sequence_number').first()
            self.sequence_number = (last.sequence_number + 1) if last else 1
        super().save(*args, **kwargs)


class SecurityArticleAttachment(models.Model):
    article = models.ForeignKey(SecurityArticle, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='blog/security/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
