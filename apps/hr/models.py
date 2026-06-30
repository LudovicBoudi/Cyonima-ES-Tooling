from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments', verbose_name='Responsable')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('essai', 'Période d\'essai'),
        ('absent', 'Absent'),
        ('conges', 'En congés'),
        ('suspension', 'Suspension'),
        ('sorti', 'Sorti'),
    ]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_employee', verbose_name='Utilisateur associé')
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Téléphone', max_length=50, blank=True)
    mobile = models.CharField('Portable', max_length=50, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name='Département')
    job_title = models.CharField('Poste', max_length=200, blank=True)
    hire_date = models.DateField("Date d'embauche", null=True, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='actif')
    birth_date = models.DateField('Date de naissance', null=True, blank=True)
    address = models.TextField('Adresse', blank=True)
    emergency_contact = models.CharField('Contact d\'urgence', max_length=255, blank=True)
    emergency_phone = models.CharField('Tél. urgence', max_length=50, blank=True)
    company = models.CharField('Société d\'origine', max_length=255, blank=True, help_text='Pour les prestataires externes')
    notes = models.TextField('Notes', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False, related_name='created_employees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Contract(models.Model):
    TYPE_CHOICES = [
        ('cdi', 'CDI'),
        ('cdd', 'CDD'),
        ('mission', 'Mission'),
        ('stage', 'Stage'),
        ('alternance', 'Alternance'),
        ('freelance', 'Freelance'),
        ('interim', 'Intérim'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts', verbose_name='Employé')
    type = models.CharField('Type', max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField('Date de début')
    end_date = models.DateField('Date de fin', null=True, blank=True)
    salary = models.DecimalField('Salaire mensuel', max_digits=10, decimal_places=2, default=0)
    position = models.CharField('Poste', max_length=200, blank=True)
    description = models.TextField('Description', blank=True)
    document = models.FileField('Document', upload_to='hr/contracts/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contrat'
        verbose_name_plural = 'Contrats'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.employee} — {self.get_type_display()} ({self.start_date})'


class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ('cp', 'Congés payés'),
        ('rtt', 'RTT'),
        ('maladie', 'Maladie'),
        ('maternite', 'Maternité / Paternité'),
        ('sans_solde', 'Sans solde'),
        ('formation', 'Formation'),
    ]
    STATUS_CHOICES = [
        ('demande', 'Demandé'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
        ('annule', 'Annulé'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests', verbose_name='Employé')
    type = models.CharField('Type', max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField('Date de début')
    end_date = models.DateField('Date de fin')
    reason = models.TextField('Motif', blank=True)
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='demande')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves', verbose_name='Validé par')
    comment = models.TextField('Commentaire', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande de congé'
        verbose_name_plural = 'Demandes de congé'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee} — {self.get_type_display()} ({self.start_date} → {self.end_date})'

    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
