from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.budget.budgets.models import BudgetYear
from apps.budget.dat.models import DATLine
from apps.notifications.utils import create_notification
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Vérifie les seuils budgétaires et envoie des notifications en cas de dépassement'

    def handle(self, *args, **kwargs):
        for budget in BudgetYear.objects.all():
            consumed = float(DATLine.objects.filter(
                dat__year=budget.year, budget_type=budget.budget_type
            ).aggregate(s=Sum('global_price'))['s'] or 0)
            allocated = float(budget.amount)
            if not allocated:
                continue

            pct = round(consumed / allocated * 100, 1)
            if pct >= 100:
                level = 'dépassé'
            elif pct >= 80:
                level = 'critique'
            else:
                continue

            users = UserProfile.objects.filter(roles__code__in=['admin', 'it_manager'])
            for profile in users:
                create_notification(
                    profile.user,
                    f'Budget {budget.get_budget_type_display()} {budget.year} — {level}',
                    f'Consommation : {consumed:,.0f}€ / {allocated:,.0f}€ ({pct}%)',
                    link='/budget/dashboard/',
                )
            self.stdout.write(f'Budget {budget}: {pct}% — {len(users)} notif(s) envoyée(s)')
        self.stdout.write('Vérification terminée.')
