from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import BudgetYear
from decimal import Decimal


@login_required
def budget_list(request):
    budgets = BudgetYear.objects.all().order_by('-year', 'budget_type')
    return render(request, 'budget/budget_list.html', {'budgets': budgets})


@login_required
def budget_create(request):
    if request.method == 'POST':
        try:
            year = int(request.POST.get('year', ''))
            budget_type = request.POST.get('budget_type', '')
            amount_str = request.POST.get('amount', '')
            if not budget_type:
                raise ValueError("Type de budget requis.")
            amount = Decimal(amount_str) if amount_str else Decimal('0')
        except (ValueError, TypeError):
            messages.error(request, "Valeurs invalides. Vérifiez l'année et le montant.")
            return render(request, 'budget/budget_form.html', {'title': 'Nouveau budget'})
        if BudgetYear.objects.filter(year=year, budget_type=budget_type).exists():
            messages.error(request, f'Un budget {budget_type} existe déjà pour {year}.')
            return render(request, 'budget/budget_form.html', {'title': 'Nouveau budget', 'budget': {'year': year, 'budget_type': budget_type, 'amount': amount}})
        BudgetYear.objects.create(year=year, budget_type=budget_type, amount=amount)
        messages.success(request, 'Budget créé.')
        return redirect('budget_list')
    return render(request, 'budget/budget_form.html', {'title': 'Nouveau budget'})


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(BudgetYear, pk=pk)
    if request.method == 'POST':
        try:
            year = int(request.POST.get('year', ''))
            budget_type = request.POST.get('budget_type', '')
            amount_str = request.POST.get('amount', '')
            if not budget_type:
                raise ValueError("Type de budget requis.")
            amount = Decimal(amount_str) if amount_str else Decimal('0')
        except (ValueError, TypeError):
            messages.error(request, "Valeurs invalides. Vérifiez l'année et le montant.")
            return render(request, 'budget/budget_form.html', {'budget': budget, 'title': 'Modifier budget'})
        if BudgetYear.objects.filter(year=year, budget_type=budget_type).exclude(pk=pk).exists():
            messages.error(request, f'Un budget {budget_type} existe déjà pour {year}.')
            return render(request, 'budget/budget_form.html', {'budget': budget, 'title': 'Modifier budget'})
        budget.year = year
        budget.budget_type = budget_type
        budget.amount = amount
        budget.save()
        messages.success(request, 'Budget modifié.')
        return redirect('budget_list')
    return render(request, 'budget/budget_form.html', {'budget': budget, 'title': 'Modifier budget'})


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(BudgetYear, pk=pk)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget supprimé.')
        return redirect('budget_list')
    return render(request, 'budget/budget_confirm_delete.html', {'budget': budget})
