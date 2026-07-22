from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from collections import OrderedDict
from apps.crm.models import Company, Contact, Deal
from apps.budget.providers.models import Provider


def _next_number(prefix, model_cls):
    with transaction.atomic():
        last = model_cls.objects.select_for_update().filter(number__startswith=prefix).order_by('number').last()
        if last and '-' in last.number:
            seq = int(last.number.split('-')[-1]) + 1
        else:
            seq = 1
        return f'{prefix}-{seq:04d}'

TWO_PLACES = Decimal('0.01')


def _quantize(val):
    return Decimal(str(val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def vat_breakdown(lines):
    rates = OrderedDict()
    for l in lines:
        ht = Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
        rate = Decimal(str(l.get('vat_rate', 20)))
        if rate not in rates:
            rates[rate] = {'ht': Decimal('0'), 'vat': Decimal('0')}
        rates[rate]['ht'] += ht
        rates[rate]['vat'] += ht * rate / Decimal('100')
    return rates


class Product(models.Model):
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    unit_price = models.DecimalField('Prix unitaire HT', max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField('Taux TVA (%)', max_digits=4, decimal_places=1, default=20)
    category = models.CharField('Catégorie', max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} — {self.unit_price} €'


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]
    number = models.CharField('Numéro', max_length=50, unique=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations', verbose_name='Société')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations', verbose_name='Contact')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations', verbose_name='Affaire CRM')
    date = models.DateField('Date', auto_now_add=True)
    valid_until = models.DateField('Valable jusqu\'au', null=True, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='brouillon')
    lines = models.JSONField('Lignes', default=list, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Devis'
        verbose_name_plural = 'Devis'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_number('DEV', Quotation)
        super().save(*args, **kwargs)

    def total_ht(self):
        return sum(
            Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            for l in self.lines
        )

    def total_tva(self):
        total = Decimal('0')
        for l in self.lines:
            ht = Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            rate = Decimal(str(l.get('vat_rate', 20)))
            total += ht * rate / Decimal('100')
        return _quantize(total)

    def total_ttc(self):
        return _quantize(self.total_ht() + self.total_tva())

    def __str__(self):
        return f'{self.number}'


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('emise', 'Émise'),
        ('payee', 'Payée'),
        ('impayee', 'Impayée'),
        ('annulee', 'Annulée'),
    ]
    number = models.CharField('Numéro', max_length=50, unique=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name='Société')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name='Contact')
    date = models.DateField('Date', auto_now_add=True)
    due_date = models.DateField('Date d\'échéance', null=True, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='brouillon')
    lines = models.JSONField('Lignes', default=list, blank=True)
    paid_amount = models.DecimalField('Montant payé', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name='Devis')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facture client'
        verbose_name_plural = 'Factures clients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_number('FACT', Invoice)
        super().save(*args, **kwargs)

    def total_ht(self):
        return sum(
            Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            for l in self.lines
        )

    def total_tva(self):
        total = Decimal('0')
        for l in self.lines:
            ht = Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            rate = Decimal(str(l.get('vat_rate', 20)))
            total += ht * rate / Decimal('100')
        return _quantize(total)

    def total_ttc(self):
        return _quantize(self.total_ht() + self.total_tva())

    def remaining(self):
        return _quantize(self.total_ttc() - self.paid_amount)

    @property
    def is_overdue(self):
        from django.utils import timezone
        return (
            self.due_date is not None
            and self.due_date < timezone.now().date()
            and self.remaining() > 0
        )

    def __str__(self):
        return f'{self.number}'


class CreditNote(models.Model):
    number = models.CharField('Numéro', max_length=50, unique=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_notes', verbose_name='Société')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_notes', verbose_name='Facture')
    date = models.DateField('Date', auto_now_add=True)
    reason = models.TextField('Motif', blank=True)
    lines = models.JSONField('Lignes', default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avoir'
        verbose_name_plural = 'Avoirs'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_number('AVOIR', CreditNote)
        super().save(*args, **kwargs)

    def total_ht(self):
        return sum(
            Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            for l in self.lines
        )

    def total_tva(self):
        total = Decimal('0')
        for l in self.lines:
            ht = Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            rate = Decimal(str(l.get('vat_rate', 20)))
            total += ht * rate / Decimal('100')
        return _quantize(total)

    def total_ttc(self):
        return _quantize(self.total_ht() + self.total_tva())

    def __str__(self):
        return f'{self.number}'


class SupplierInvoice(models.Model):
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('enregistree', 'Enregistrée'),
        ('payee', 'Payée'),
    ]
    number = models.CharField('Numéro fournisseur', max_length=100, blank=True)
    internal_number = models.CharField('Numéro interne', max_length=50, unique=True, editable=False)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name='Fournisseur')
    date = models.DateField('Date')
    due_date = models.DateField('Date d\'échéance', null=True, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='brouillon')
    lines = models.JSONField('Lignes', default=list, blank=True)
    paid_amount = models.DecimalField('Montant payé', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facture fournisseur'
        verbose_name_plural = 'Factures fournisseurs'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.internal_number:
            self.internal_number = _next_number('FACF', SupplierInvoice)
        super().save(*args, **kwargs)

    def total_ht(self):
        return sum(
            Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            for l in self.lines
        )

    def total_tva(self):
        total = Decimal('0')
        for l in self.lines:
            ht = Decimal(str(l.get('quantity', 0))) * Decimal(str(l.get('unit_price', 0)))
            rate = Decimal(str(l.get('vat_rate', 20)))
            total += ht * rate / Decimal('100')
        return _quantize(total)

    def total_ttc(self):
        return _quantize(self.total_ht() + self.total_tva())

    def remaining(self):
        return _quantize(self.total_ttc() - self.paid_amount)

    def __str__(self):
        return f'{self.internal_number}'


class Payment(models.Model):
    METHOD_CHOICES = [
        ('carte', 'Carte bancaire'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('prelevement', 'Prélèvement'),
    ]
    date = models.DateField('Date')
    amount = models.DecimalField('Montant', max_digits=12, decimal_places=2)
    method = models.CharField('Mode', max_length=20, choices=METHOD_CHOICES, default='virement')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='Facture client')
    supplier_invoice = models.ForeignKey(SupplierInvoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='Facture fournisseur')
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} — {self.amount}€'


class Reminder(models.Model):
    LEVEL_CHOICES = [
        (1, '1ʳᵉ relance'),
        (2, '2ᵉ relance'),
        (3, '3ᵉ relance'),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders', verbose_name='Facture')
    level = models.PositiveSmallIntegerField('Niveau', choices=LEVEL_CHOICES, default=1)
    date = models.DateField('Date', auto_now_add=True)
    amount_due = models.DecimalField('Montant dû', max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        verbose_name = 'Relance'
        verbose_name_plural = 'Relances'
        ordering = ['-date']

    def __str__(self):
        return f'{self.invoice.number} — Niveau {self.level} ({self.date})'


class ErpAuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('edit', 'Modification'),
        ('delete', 'Suppression'),
        ('convert', 'Conversion devis→facture'),
        ('payment', 'Paiement'),
        ('reminder', 'Relance'),
        ('export', 'Export'),
    ]
    model_name = models.CharField('Modèle', max_length=50)
    object_id = models.PositiveIntegerField('ID objet')
    object_repr = models.CharField('Représentation', max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField('Action', max_length=20, choices=ACTION_CHOICES)
    details = models.TextField('Détails', blank=True)
    ip_address = models.GenericIPAddressField('IP', blank=True, null=True)
    created_at = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'audit ERP"
        verbose_name_plural = "Journaux d'audit ERP"
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} — {self.object_repr} ({self.created_at.strftime("%d/%m/%Y %H:%M")})'


class RecurringInvoice(models.Model):
    FREQ_CHOICES = [
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('yearly', 'Annuelle'),
    ]
    title = models.CharField('Titre', max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recurring_invoices', verbose_name='Société')
    lines = models.JSONField('Lignes', default=list, blank=True)
    frequency = models.CharField('Fréquence', max_length=20, choices=FREQ_CHOICES, default='monthly')
    next_date = models.DateField('Prochaine échéance')
    is_active = models.BooleanField('Actif', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Facture récurrente'
        verbose_name_plural = 'Factures récurrentes'
        ordering = ['next_date']

    def __str__(self):
        return f'{self.title} ({self.company})'


class QuotationTemplate(models.Model):
    name = models.CharField('Nom', max_length=255)
    lines = models.JSONField('Lignes', default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Modèle de devis'
        verbose_name_plural = 'Modèles de devis'
        ordering = ['name']

    def __str__(self):
        return self.name
