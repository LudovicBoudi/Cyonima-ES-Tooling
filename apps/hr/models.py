from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
    grade = models.CharField('Grade (Ccn. Métallurgie)', max_length=4, blank=True, choices=[
        ('A1', 'A1'), ('A2', 'A2'),
        ('B3', 'B3'), ('B4', 'B4'),
        ('C5', 'C5'), ('C6', 'C6'),
        ('D7', 'D7'), ('D8', 'D8'),
        ('E9', 'E9'), ('E10', 'E10'),
        ('F11', 'F11'), ('F12', 'F12'),
        ('G13', 'G13'), ('G14', 'G14'),
        ('H15', 'H15'), ('H16', 'H16'),
        ('I17', 'I17'), ('I18', 'I18'),
    ])
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


DIPLOMA_LEVELS = [
    ('bepc', 'BEPC'),
    ('bep', 'BEP'),
    ('cap', 'CAP'),
    ('bac', 'BAC'),
    ('bac+2', 'BAC+2'),
    ('bac+3', 'BAC+3'),
    ('bac+5', 'BAC+5'),
    ('doctorat', 'Doctorat'),
]


class Diploma(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='diplomas', verbose_name='Employé')
    level = models.CharField('Niveau', max_length=20, choices=DIPLOMA_LEVELS)
    name = models.CharField('Nom du diplôme', max_length=255)
    school = models.CharField('Établissement', max_length=255)
    year = models.PositiveIntegerField('Année d\'obtention')
    file = models.FileField('Copie du diplôme', upload_to='hr/diplomas/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diplôme'
        verbose_name_plural = 'Diplômes'
        ordering = ['-year', 'name']

    def __str__(self):
        return f'{self.get_level_display()} — {self.name} ({self.year})'


class Certification(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certifications', verbose_name='Employé')
    name = models.CharField('Nom de la certification', max_length=255)
    company = models.CharField('Organisme émetteur', max_length=255)
    year = models.PositiveIntegerField('Année d\'obtention')
    file = models.FileField('Copie de la certification', upload_to='hr/certifications/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Certification'
        verbose_name_plural = 'Certifications'
        ordering = ['-year', 'name']

    def __str__(self):
        return f'{self.name} ({self.year})'


class Training(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='trainings', verbose_name='Employé')
    name = models.CharField('Nom de la formation', max_length=255)
    organization = models.CharField('Organisme de formation', max_length=255)
    year = models.PositiveIntegerField('Année de réalisation')
    file = models.FileField('Attestation de formation', upload_to='hr/trainings/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        ordering = ['-year', 'name']

    def __str__(self):
        return f'{self.name} ({self.year})'


class Employment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employments', verbose_name='Employé')
    job_title = models.CharField('Titre du poste', max_length=255)
    employer = models.CharField('Employeur', max_length=255)
    description = models.TextField('Description des fonctions', blank=True)
    start_date = models.DateField('Date de début')
    end_date = models.DateField('Date de fin', blank=True, null=True)

    class Meta:
        verbose_name = 'Emploi précédent'
        verbose_name_plural = 'Emplois précédents'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.job_title} chez {self.employer}'

    @property
    def duration(self):
        from datetime import date
        end = self.end_date or date.today()
        delta = end - self.start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        if years and months:
            return f'{years} an{"s" if years > 1 else ""} {months} mois'
        if years:
            return f'{years} an{"s" if years > 1 else ""}'
        if months:
            return f'{months} mois'
        return f'{delta.days} jour{"s" if delta.days > 1 else ""}'


class Cv(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='cvs', verbose_name='Employé')
    file = models.FileField('CV', upload_to='hr/cvs/')
    uploaded_at = models.DateTimeField('Date d\'upload', auto_now_add=True)

    class Meta:
        verbose_name = 'CV'
        verbose_name_plural = 'CVs'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'CV du {self.uploaded_at.strftime("%d/%m/%Y")}'


class Evaluation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='evaluations', verbose_name='Employé')
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Évaluateur')
    year = models.PositiveIntegerField('Année d\'évaluation')
    rating = models.PositiveIntegerField('Note', choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField('Avis', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f'{self.employee} — {self.year} : {self.rating}/5'


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

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('La date de fin ne peut pas être antérieure à la date de début.')

    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
