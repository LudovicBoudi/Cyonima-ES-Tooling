import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Q
from apps.budget.dat.models import DATLine
from apps.budget.budgets.models import BudgetYear


@login_required
def dashboard(request):
    years = list(BudgetYear.objects.values_list('year', flat=True).distinct().order_by('-year'))
    selected_year = request.GET.get('year')
    if not selected_year and years:
        selected_year = str(years[0])
    elif not selected_year:
        from django.utils import timezone
        selected_year = str(timezone.now().year)

    category_labels = [
        ('licences', 'Licences'), ('maintenance', 'Maintenance'),
        ('pc', 'PC'), ('servers', 'Serveurs'),
        ('network', 'Réseau'), ('security', 'Sécurité'),
        ('consulting', 'Consulting'),
    ]

    budget_data = []
    if selected_year:
        year_int = int(selected_year)
        budgets = {b.budget_type: float(b.amount) for b in BudgetYear.objects.filter(year=year_int)}
        cat_sums = {}
        for row in DATLine.objects.filter(dat__year=year_int).values('budget_type', 'budget_category').annotate(s=Sum('global_price')):
            key = (row['budget_type'], row['budget_category'])
            cat_sums[key] = float(row['s'] or 0)

        for bt_code, bt_label in [('investment', 'Investissement'), ('fonctionnement', 'Fonctionnement')]:
            allocated = budgets.get(bt_code, 0)
            consumed_vals = []
            consumed_alerts = []
            total_consumed = 0
            for cat_code, cat_label in category_labels:
                val = cat_sums.get((bt_code, cat_code), 0)
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

    evolution_labels = []
    evolution_invest_alloc = []
    evolution_invest_cons = []
    evolution_run_alloc = []
    evolution_run_cons = []
    all_budgets = {b.year: {} for b in BudgetYear.objects.filter(year__in=years)}
    for b in BudgetYear.objects.filter(year__in=years):
        all_budgets.setdefault(b.year, {})[b.budget_type] = float(b.amount)
    all_cons = {}
    for row in DATLine.objects.values('dat__year', 'budget_type').annotate(s=Sum('global_price')):
        all_cons[(row['dat__year'], row['budget_type'])] = float(row['s'] or 0)

    for y in reversed(sorted(years)):
        evolution_labels.append(str(y))
        evolution_invest_alloc.append(all_budgets.get(y, {}).get('investment', 0))
        evolution_invest_cons.append(all_cons.get((y, 'investment'), 0))
        evolution_run_alloc.append(all_budgets.get(y, {}).get('fonctionnement', 0))
        evolution_run_cons.append(all_cons.get((y, 'fonctionnement'), 0))

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
