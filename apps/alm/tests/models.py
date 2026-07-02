from django.db import models
from django.contrib.auth.models import User
from apps.alm.projects.models import Project
from apps.alm.requirements.models import Requirement


class TestScenario(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_scenarios')
    number = models.IntegerField(editable=False, verbose_name='Numéro')
    name = models.CharField(max_length=255, verbose_name='Nom')
    execution_conditions = models.TextField(blank=True, verbose_name='Conditions d\'exécution')
    description = models.TextField(blank=True, verbose_name='Description')
    requirements = models.ManyToManyField(Requirement, blank=True, related_name='test_scenarios')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scénario de test'
        verbose_name_plural = 'Scénarios de test'
        unique_together = [('project', 'number')]
        ordering = ['number']

    def __str__(self):
        return f"{self.get_formatted_number()} - {self.name}"

    def get_formatted_number(self):
        return f"{self.number:04d}"

    def save(self, *args, **kwargs):
        if not self.pk:
            last = TestScenario.objects.filter(project=self.project).order_by('-number').first()
            self.number = (last.number + 1) if last else 1
        super().save(*args, **kwargs)


class TestStep(models.Model):
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField(verbose_name='N° étape')
    action = models.TextField(verbose_name='Action')
    expected_result = models.TextField(verbose_name='Résultat attendu')

    class Meta:
        verbose_name = 'Étape de test'
        verbose_name_plural = 'Étapes de test'
        unique_together = [('test_scenario', 'step_number')]
        ordering = ['step_number']

    def __str__(self):
        return f"Étape {self.step_number}"


class TestCampaign(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campagne de test'
        verbose_name_plural = 'Campagnes de test'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CampaignTest(models.Model):
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('en_cours', 'En cours'),
        ('verifie', 'Vérifié'),
        ('valide', 'Validé'),
    ]
    campaign = models.ForeignKey(TestCampaign, on_delete=models.CASCADE, related_name='tests')
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog', verbose_name='Statut')
    position = models.IntegerField(default=0, verbose_name='Position')

    class Meta:
        verbose_name = 'Test de campagne'
        verbose_name_plural = 'Tests de campagne'
        unique_together = [('campaign', 'test_scenario')]
        ordering = ['position']

    def __str__(self):
        return f"{self.test_scenario.name} - {self.get_status_display()}"


class TestAttachment(models.Model):
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='tests/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'

    def __str__(self):
        return self.filename


class TestExecution(models.Model):
    RESULT_CHOICES = [
        ('reussi', 'Réussi'),
        ('en_echec', 'En échec'),
        ('bloque', 'Bloqué'),
        ('non_execute', 'Non exécuté'),
    ]
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='non_execute', verbose_name='Résultat')
    notes = models.TextField(blank=True, verbose_name='Notes')
    step_results = models.JSONField(default=dict, blank=True, verbose_name='Résultats par étape')
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exécution de test'
        verbose_name_plural = 'Exécutions de test'
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.test_scenario} - {self.get_result_display()} ({self.executed_at})"
