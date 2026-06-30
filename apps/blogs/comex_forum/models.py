from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ComexThread(models.Model):
    year = models.IntegerField(editable=False)
    sequence_number = models.IntegerField(editable=False)
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comex_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fil COMEX'
        verbose_name_plural = 'Fils COMEX'
        unique_together = [('year', 'sequence_number')]
        ordering = ['-year', '-sequence_number']

    def __str__(self):
        return self.display_id()

    def display_id(self):
        return f"COMEX-{self.year}-{self.sequence_number:04d}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.year = timezone.now().year
            last = ComexThread.objects.filter(year=self.year).order_by('-sequence_number').first()
            self.sequence_number = (last.sequence_number + 1) if last else 1
        super().save(*args, **kwargs)


class ComexMessage(models.Model):
    thread = models.ForeignKey(ComexThread, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(max_length=4000)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message COMEX'
        verbose_name_plural = 'Messages COMEX'
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.created_by.username} - {self.created_at.date()}"


class ComexAttachment(models.Model):
    message = models.ForeignKey(ComexMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='comex/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
