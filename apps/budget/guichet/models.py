from django.db import models
from django.contrib.auth.models import User


class GuichetTicket(models.Model):
    TYPES = [
        ('incident', 'Incident'),
        ('ebi', 'Expression de Besoin Informatique'),
    ]

    WORKFLOWS = {
        'incident': {
            'nouveau': ['en_cours'],
            'en_cours': ['resolu', 'nouveau'],
            'resolu': ['ferme', 'en_cours'],
            'ferme': [],
        },
        'ebi': {
            'nouveau': ['en_etude'],
            'en_etude': ['valide', 'nouveau'],
            'valide': ['realise', 'en_etude'],
            'realise': ['ferme', 'valide'],
            'ferme': [],
        },
    }

    TYPE_PREFIXES = {
        'incident': 'INC',
        'ebi': 'EBI',
    }

    STATUS_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('en_etude', 'En étude'),
        ('resolu', 'Résolu'),
        ('valide', 'Validé'),
        ('realise', 'Réalisé'),
        ('ferme', 'Fermé'),
    ]

    ticket_type = models.CharField(max_length=20, choices=TYPES, verbose_name='Type')
    number = models.IntegerField(editable=False, verbose_name='Numéro')
    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guichet_tickets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nouveau', verbose_name='Statut')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_guichet_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket guichet'
        verbose_name_plural = 'Tickets guichet'
        unique_together = [('ticket_type', 'number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_formatted_number()} - {self.title}"

    def get_formatted_number(self):
        prefix = self.TYPE_PREFIXES.get(self.ticket_type, 'TKT')
        return f"{prefix}-{self.number:04d}"

    def get_available_statuses(self):
        workflow = self.WORKFLOWS.get(self.ticket_type, {})
        return workflow.get(self.status, [])

    def save(self, *args, **kwargs):
        if not self.pk:
            last = GuichetTicket.objects.filter(ticket_type=self.ticket_type).order_by('-number').first()
            self.number = (last.number + 1) if last else 1
            self.status = 'nouveau'
        super().save(*args, **kwargs)


class GuichetLog(models.Model):
    ticket = models.ForeignKey(GuichetTicket, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20, blank=True, null=True)
    to_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique guichet'
        verbose_name_plural = 'Historiques guichet'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket.get_formatted_number()} - {self.from_status} → {self.to_status}"
