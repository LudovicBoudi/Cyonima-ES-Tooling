from django.db import models


class Provider(models.Model):
    company_name = models.CharField(max_length=255, verbose_name='Entreprise')
    sales_contact = models.CharField(max_length=255, verbose_name='Contact commercial')
    phone = models.CharField(max_length=50, verbose_name='Téléphone')
    email = models.EmailField(verbose_name='Email')
    description = models.TextField(blank=True, verbose_name='Description')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fournisseur'
        verbose_name_plural = 'Fournisseurs'
        ordering = ['company_name']

    def __str__(self):
        return self.company_name
