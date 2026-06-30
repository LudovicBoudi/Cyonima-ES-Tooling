from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from .models import GuichetTicket, GuichetLog
from django.contrib.auth.models import User


@login_required
def ticket_list(request):
    current_type = request.GET.get('type', 'incident')
    tickets = GuichetTicket.objects.filter(ticket_type=current_type)
    return render(request, 'budget/guichet_list.html', {
        'tickets': tickets,
        'current_type': current_type,
    })


@login_required
def ticket_create(request):
    if request.method == 'POST':
        try:
            ticket = GuichetTicket.objects.create(
                ticket_type=request.POST['ticket_type'],
                title=request.POST['title'],
                description=request.POST.get('description', ''),
                assigned_to_id=request.POST.get('assigned_to') or None,
                created_by=request.user,
            )
            messages.success(request, f'Ticket {ticket.get_formatted_number()} créé.')
            return redirect('guichet_list')
        except IntegrityError:
            messages.error(request, 'Erreur lors de la création.')
    users = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'budget/guichet_form.html', {
        'title': 'Nouveau ticket',
        'users': users,
    })


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(GuichetTicket, pk=pk)
    transitions = ticket.get_available_statuses()
    logs = ticket.logs.all()

    if request.method == 'POST' and 'transition' in request.POST:
        to_status = request.POST['transition']
        if to_status in transitions:
            GuichetLog.objects.create(
                ticket=ticket,
                user=request.user,
                from_status=ticket.status,
                to_status=to_status,
                comment=request.POST.get('comment', ''),
            )
            ticket.status = to_status
            ticket.save()
            messages.success(request, f'Statut mis à jour → {to_status}')
            return redirect('guichet_detail', pk=pk)
        else:
            messages.error(request, 'Transition invalide.')

    return render(request, 'budget/guichet_detail.html', {
        'ticket': ticket,
        'transitions': transitions,
        'logs': logs,
    })
