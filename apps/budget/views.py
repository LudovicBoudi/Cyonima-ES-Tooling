from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def budget_home(request):
    return redirect('budget_dashboard')
