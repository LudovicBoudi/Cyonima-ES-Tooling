from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class WikiPage(models.Model):
    title = models.CharField(max_length=255, verbose_name='Titre')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    content = models.TextField(verbose_name='Contenu')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wiki_pages')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='wiki_edits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Page wiki'
        verbose_name_plural = 'Pages wiki'
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            counter = 1
            while WikiPage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
