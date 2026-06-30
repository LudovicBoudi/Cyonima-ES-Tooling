import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from apps.budget.dat.models import DATLine
from apps.budget.budgets.models import BudgetYear
from datetime import datetime


@login_required
def dashboard(request):
    years = list(BudgetYear.objects.values_list('year', flat=True).distinct().order_by('-year'))
    selected_year = request.GET.get('year')
    if not selected_year and years:
        selected_year = str(years[0])

    category_labels = [
        ('licences', 'Licences'), ('maintenance', 'Maintenance'),
        ('pc', 'PC'), ('servers', 'Serveurs'),
        ('network', 'Réseau'), ('security', 'Sécurité'),
        ('consulting', 'Consulting'),
    ]

    budget_data = []
    if selected_year:
        year_int = int(selected_year)
        for bt_code, bt_label in [('investment', 'Investissement'), ('fonctionnement', 'Fonctionnement')]:
            try:
                budget_obj = BudgetYear.objects.get(year=year_int, budget_type=bt_code)
                allocated = float(budget_obj.amount)
            except BudgetYear.DoesNotExist:
                allocated = 0

            consumed_vals = []
            consumed_alerts = []
            total_consumed = 0
            for cat_code, cat_label in category_labels:
                val = float(DATLine.objects.filter(
                    dat__year=year_int, budget_type=bt_code, budget_category=cat_code
                ).aggregate(s=Sum('global_price'))['s'] or 0)
                consumed_vals.append(val)
                pct = round(val / allocated * 100, 1) if allocated else 0
                if pct >= 100:
                    level = 'danger'
                elif pct >= 80:
                    level = 'warning'
                else:
                    level = 'success'
                consumed_alerts.append((cat_label, val, pct, level))
                total_consumed += val

            remaining = max(0, allocated - total_consumed)
            overall_pct = round(total_consumed / allocated * 100, 1) if allocated else 0
            overall_level = 'danger' if overall_pct >= 100 else ('warning' if overall_pct >= 80 else 'success')

            budget_data.append({
                'type': bt_label,
                'type_code': bt_code,
                'allocated': allocated,
                'total_consumed': total_consumed,
                'consumed_vals': consumed_vals,
                'consumed_alerts': consumed_alerts,
                'remaining': remaining,
                'overall_pct': overall_pct,
                'overall_level': overall_level,
                'consumed_json': json.dumps(consumed_vals),
                'remaining_json': json.dumps([total_consumed, remaining]),
            })

    # Multi-year evolution
    evolution_labels = []
    evolution_invest_alloc = []
    evolution_invest_cons = []
    evolution_run_alloc = []
    evolution_run_cons = []
    for y in reversed(sorted(years)):
        evolution_labels.append(str(y))
        for bt_code, alloc_list, cons_list in [
            ('investment', evolution_invest_alloc, evolution_invest_cons),
            ('fonctionnement', evolution_run_alloc, evolution_run_cons),
        ]:
            try:
                alloc_list.append(float(BudgetYear.objects.get(year=y, budget_type=bt_code).amount))
            except BudgetYear.DoesNotExist:
                alloc_list.append(0)
            consumed = float(DATLine.objects.filter(
                dat__year=y, budget_type=bt_code
            ).aggregate(s=Sum('global_price'))['s'] or 0)
            cons_list.append(consumed)

    return render(request, 'budget/dashboard.html', {
        'budget_data': budget_data,
        'years': years,
        'selected_year': selected_year,
        'category_labels': category_labels,
        'evolution_labels': json.dumps(evolution_labels),
        'evolution_invest_alloc': json.dumps(evolution_invest_alloc),
        'evolution_invest_cons': json.dumps(evolution_invest_cons),
        'evolution_run_alloc': json.dumps(evolution_run_alloc),
        'evolution_run_cons': json.dumps(evolution_run_cons),
    })
