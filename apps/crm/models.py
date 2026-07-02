from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from decimal import Decimal


class Company(models.Model):
    name = models.CharField('Nom', max_length=255)
    sector = models.CharField('Secteur', max_length=200, blank=True)
    address = models.CharField('Adresse', max_length=300, blank=True)
    postal_code = models.CharField('Code postal', max_length=20, blank=True)
    city = models.CharField('Ville', max_length=100, blank=True)
    country = models.CharField('Pays', max_length=100, blank=True, default='France')
    website = models.URLField('Site web', blank=True)
    phone = models.CharField('Téléphone', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    siret = models.CharField('SIRET', max_length=14, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Société'
        verbose_name_plural = 'Sociétés'
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts', verbose_name='Société', null=True, blank=True)
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Téléphone', max_length=50, blank=True)
    mobile = models.CharField('Portable', max_length=50, blank=True)
    function = models.CharField('Fonction', max_length=200, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Deal(models.Model):
    STAGE_CHOICES = [
        ('prospection', 'Prospection'),
        ('devis', 'Devis'),
        ('negociation', 'Négociation'),
        ('gagne', 'Gagné'),
        ('perdu', 'Perdu'),
    ]
    title = models.CharField('Titre', max_length=255)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals', verbose_name='Société')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals', verbose_name='Contact')
    amount = models.DecimalField('Montant', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    probability = models.PositiveSmallIntegerField('Probabilité (%)', default=0)
    stage = models.CharField('Étape', max_length=20, choices=STAGE_CHOICES, default='prospection')
    expected_close_date = models.DateField('Date de clôture prévue', null=True, blank=True)
    description = models.TextField('Description', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Affaire'
        verbose_name_plural = 'Affaires'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DealStageLog(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='stage_logs')
    from_stage = models.CharField('Étape précédente', max_length=20, blank=True)
    to_stage = models.CharField('Nouvelle étape', max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique d\'étape'
        verbose_name_plural = 'Historique des étapes'
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.deal.title}: {self.from_stage or "-"} → {self.to_stage}'


class Interaction(models.Model):
    TYPE_CHOICES = [
        ('appel', 'Appel'),
        ('email', 'Email'),
        ('reunion', 'Réunion'),
        ('note', 'Note'),
    ]
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='interactions', verbose_name='Contact')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions', verbose_name='Affaire')
    type = models.CharField('Type', max_length=10, choices=TYPE_CHOICES, default='note')
    subject = models.CharField('Sujet', max_length=255)
    content = models.TextField('Contenu', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_type_display()}] {self.subject}'


class CrmTask(models.Model):
    title = models.CharField('Titre', max_length=255)
    description = models.TextField('Description', blank=True)
    due_date = models.DateField('Échéance', null=True, blank=True)
    completed = models.BooleanField('Terminée', default=False)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name='Contact')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name='Affaire')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_tasks', verbose_name='Assigné à')
    reminder_date = models.DateTimeField('Rappel', null=True, blank=True)
    reminder_sent = models.BooleanField('Rappel envoyé', default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False, related_name='created_crm_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tâche CRM'
        verbose_name_plural = 'Tâches CRM'
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title


class CrmAttachment(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    interaction = models.ForeignKey(Interaction, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField('Fichier', upload_to='crm/attachments/%Y/%m/')
    filename = models.CharField('Nom du fichier', max_length=255, editable=False)
    file_size = models.PositiveIntegerField('Taille (octets)', editable=False, default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name.split('/')[-1]
            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.filename
