from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.budget.providers.models import Provider


class DAT(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('validated', 'Validé'),
        ('rejected', 'Refusé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Statut')
    sequence_number = models.IntegerField(editable=False, verbose_name='Numéro séquence')
    year = models.IntegerField(editable=False, verbose_name='Année')
    created_date = models.DateField(auto_now_add=True, verbose_name='Date création')
    description = models.TextField(blank=True, verbose_name='Description')
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, verbose_name='Fournisseur')
    provider_contact_name = models.CharField(max_length=255, verbose_name='Nom du contact')
    provider_contact_email = models.EmailField(verbose_name='Email du contact')
    provider_contact_phone = models.CharField(max_length=50, verbose_name='Téléphone du contact')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'DAT'
        verbose_name_plural = 'DAT'
        unique_together = [('sequence_number', 'year')]
        ordering = ['-year', '-sequence_number']

    def __str__(self):
        return self.display_id()

    def display_id(self):
        return f"IT-{self.sequence_number:04d}-{self.year}"

    def total_cost(self):
        return sum(line.global_price for line in self.lines.all())

    def consumption_by_category(self):
        result = {}
        for line in self.lines.all():
            if line.global_price:
                key = (line.budget_type, line.budget_category)
                result[key] = result.get(key, 0) + line.global_price
        return result

    def save(self, *args, **kwargs):
        if not self.pk:
            self.year = timezone.now().year
            last = DAT.objects.filter(year=self.year).order_by('-sequence_number').first()
            self.sequence_number = (last.sequence_number + 1) if last else 1
        super().save(*args, **kwargs)

    def duplicate(self):
        new_dat = DAT(
            status='draft',
            provider=self.provider,
            description=self.description,
            provider_contact_name=self.provider_contact_name,
            provider_contact_email=self.provider_contact_email,
            provider_contact_phone=self.provider_contact_phone,
        )
        new_dat.save()
        for line in self.lines.all():
            DATLine.objects.create(
                dat=new_dat,
                product=line.product,
                reference=line.reference,
                unit=line.unit,
                quantity=line.quantity,
                unit_price=line.unit_price,
                budget_type=line.budget_type,
                budget_category=line.budget_category,
            )
        return new_dat


class DATLine(models.Model):
    UNIT_CHOICES = [
        ('U', 'Unité'),
        ('D', 'Jour'),
    ]
    BUDGET_TYPES = [
        ('investment', 'Investissement'),
        ('fonctionnement', 'Fonctionnement'),
    ]
    BUDGET_CATEGORIES = [
        ('licences', 'Licences'),
        ('maintenance', 'Maintenance'),
        ('pc', 'PC'),
        ('servers', 'Serveurs'),
        ('network', 'Réseau'),
        ('security', 'Sécurité'),
        ('consulting', 'Conseil'),
    ]
    dat = models.ForeignKey(DAT, on_delete=models.CASCADE, related_name='lines', verbose_name='DAT')
    product = models.CharField(max_length=255, verbose_name='Produit')
    reference = models.CharField(max_length=255, blank=True, verbose_name='Référence')
    unit = models.CharField(max_length=1, choices=UNIT_CHOICES, default='U', verbose_name='Unité')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Quantité')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Prix unitaire')
    global_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name='Total')
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES, verbose_name='Type budget')
    budget_category = models.CharField(max_length=20, choices=BUDGET_CATEGORIES, verbose_name='Catégorie')

    class Meta:
        verbose_name = 'Ligne DAT'
        verbose_name_plural = 'Lignes DAT'
        ordering = ['id']

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.global_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class DATTtemplate(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, verbose_name='Fournisseur')
    lines = models.JSONField(default=list, blank=True, verbose_name='Lignes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Modèle de DAT'
        verbose_name_plural = 'Modèles de DAT'
        ordering = ['name']

    def __str__(self):
        return self.name
