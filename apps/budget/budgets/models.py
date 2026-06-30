from django.db import models
from django.core.validators import MinValueValidator


class BudgetYear(models.Model):
    BUDGET_TYPES = [
        ('investment', 'Investissement'),
        ('fonctionnement', 'Fonctionnement'),
    ]
    year = models.IntegerField(verbose_name='Année')
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES, verbose_name='Type')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Montant alloué')

    class Meta:
        verbose_name = 'Budget annuel'
        verbose_name_plural = 'Budgets annuels'
        unique_together = [('year', 'budget_type')]
        ordering = ['-year', 'budget_type']

    def __str__(self):
        return f"{self.year} - {self.get_budget_type_display()} ({self.amount} €)"
