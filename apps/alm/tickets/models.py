from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.alm.projects.models import Project
from apps.alm.repositories.models import Repository


class Ticket(models.Model):
    TICKET_TYPES = [
        ('incident', 'Incident'),
        ('tache', 'Tâche'),
        ('ft', 'Fait technique'),
    ]

    WORKFLOWS = {
        'incident': {
            'nouveau': ['assigne'],
            'assigne': ['en_cours', 'nouveau'],
            'en_cours': ['cloture', 'assigne'],
            'cloture': [],
        },
        'tache': {
            'nouveau': ['assigne'],
            'assigne': ['en_cours', 'nouveau'],
            'en_cours': ['valide', 'assigne'],
            'valide': ['cloture', 'en_cours'],
            'cloture': [],
        },
        'ft': {
            'nouveau': ['assigne'],
            'assigne': ['en_cours', 'nouveau'],
            'en_cours': ['valide', 'assigne'],
            'valide': ['a_clore', 'en_cours'],
            'a_clore': ['cloture', 'valide'],
            'cloture': [],
        },
    }

    TYPE_PREFIXES = {
        'incident': 'INC',
        'tache': 'TCH',
        'ft': 'FT',
    }

    STATUS_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('assigne', 'Assigné'),
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('a_clore', 'À clore'),
        ('cloture', 'Clôturé'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES, verbose_name='Type')
    number = models.IntegerField(editable=False, verbose_name='Numéro')
    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nouveau', verbose_name='Statut')
    start_date = models.DateField(null=True, blank=True, verbose_name='Date début')
    due_date = models.DateField(null=True, blank=True, verbose_name='Date échéance')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closing_repository = models.ForeignKey(Repository, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Dépôt de clôture')
    closing_commit_hash = models.CharField(max_length=64, blank=True, verbose_name='Hash du commit de clôture')

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        unique_together = [('project', 'ticket_type', 'number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_formatted_number()} - {self.title}"

    def get_type_prefix(self):
        return self.TYPE_PREFIXES.get(self.ticket_type, 'TKT')

    def get_formatted_number(self):
        return f"{self.get_type_prefix()}-{self.number:04d}"

    def get_available_statuses(self):
        workflow = self.WORKFLOWS.get(self.ticket_type, {})
        return workflow.get(self.status, [])

    def save(self, *args, **kwargs):
        if not self.pk:
            last = Ticket.objects.filter(project=self.project, ticket_type=self.ticket_type).order_by('-number').first()
            self.number = (last.number + 1) if last else 1
            self.status = 'nouveau'
        super().save(*args, **kwargs)


class TicketLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20, blank=True, null=True)
    to_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    hours_spent = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name='Heures passées')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique ticket'
        verbose_name_plural = 'Historiques tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket.get_formatted_number()} - {self.from_status} → {self.to_status}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='tickets/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'

    def __str__(self):
        return self.filename


class Sprint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    start_date = models.DateField(verbose_name='Date début')
    end_date = models.DateField(verbose_name='Date fin')
    is_active = models.BooleanField(default=False, verbose_name='Actif')
    tickets = models.ManyToManyField(Ticket, blank=True, related_name='sprints')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sprint'
        verbose_name_plural = 'Sprints'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"

    def total_tickets(self):
        return self.tickets.count()

    def completed_tickets(self):
        return self.tickets.filter(status='cloture').count()

    def progress_pct(self):
        total = self.total_tickets()
        if not total:
            return 0
        return int(self.completed_tickets() / total * 100)
