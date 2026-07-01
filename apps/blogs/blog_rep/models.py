from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class RepSyndicaleArticle(models.Model):
    year = models.IntegerField(editable=False)
    sequence_number = models.IntegerField(editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(verbose_name='Contenu')
    image = models.ImageField(upload_to='blog/images/', blank=True, null=True, verbose_name='Image à la une')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article représentation syndicale'
        verbose_name_plural = 'Articles représentation syndicale'
        unique_together = [('year', 'sequence_number')]
        ordering = ['-year', '-sequence_number']

    def __str__(self):
        return self.display_id()

    def display_id(self):
        return f"REP-{self.year}-{self.sequence_number:04d}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.year = timezone.now().year
            last = RepSyndicaleArticle.objects.filter(year=self.year).order_by('-sequence_number').first()
            self.sequence_number = (last.sequence_number + 1) if last else 1
        super().save(*args, **kwargs)


class RepSyndicaleArticleAttachment(models.Model):
    article = models.ForeignKey(RepSyndicaleArticle, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='blog/rep_syndicale/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
