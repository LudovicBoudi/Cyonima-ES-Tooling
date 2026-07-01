from django.db import models
from django.contrib.auth.models import User
from apps.crm.models import Company, Contact, Deal
from apps.budget.providers.models import Provider


def _next_number(prefix, model_cls):
    last = model_cls.objects.filter(number__startswith=prefix).order_by('number').last()
    if last and '-' in last.number:
        seq = int(last.number.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}-{seq:04d}'


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
        return sum(l.get('quantity', 0) * l.get('unit_price', 0) for l in self.lines)

    def total_tva(self):
        total = 0
        for l in self.lines:
            ht = l.get('quantity', 0) * l.get('unit_price', 0)
            rate = float(l.get('vat_rate', 20))
            total += ht * rate / 100
        return round(total, 2)

    def total_ttc(self):
        return round(self.total_ht() + self.total_tva(), 2)

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
        return sum(l.get('quantity', 0) * l.get('unit_price', 0) for l in self.lines)

    def total_tva(self):
        total = 0
        for l in self.lines:
            ht = l.get('quantity', 0) * l.get('unit_price', 0)
            rate = float(l.get('vat_rate', 20))
            total += ht * rate / 100
        return round(total, 2)

    def total_ttc(self):
        return round(self.total_ht() + self.total_tva(), 2)

    def remaining(self):
        return round(self.total_ttc() - float(self.paid_amount), 2)

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
        return sum(l.get('quantity', 0) * l.get('unit_price', 0) for l in self.lines)

    def total_tva(self):
        total = 0
        for l in self.lines:
            ht = l.get('quantity', 0) * l.get('unit_price', 0)
            rate = float(l.get('vat_rate', 20))
            total += ht * rate / 100
        return round(total, 2)

    def total_ttc(self):
        return round(self.total_ht() + self.total_tva(), 2)

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
        return sum(l.get('quantity', 0) * l.get('unit_price', 0) for l in self.lines)

    def total_tva(self):
        total = 0
        for l in self.lines:
            ht = l.get('quantity', 0) * l.get('unit_price', 0)
            rate = float(l.get('vat_rate', 20))
            total += ht * rate / 100
        return round(total, 2)

    def total_ttc(self):
        return round(self.total_ht() + self.total_tva(), 2)

    def remaining(self):
        return round(self.total_ttc() - float(self.paid_amount), 2)

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
