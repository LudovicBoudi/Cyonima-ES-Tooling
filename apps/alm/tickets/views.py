from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Ticket, TicketLog
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project


@login_required
def ticket_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    ticket_type = request.GET.get('type', 'incident')
    tickets = project.tickets.filter(ticket_type=ticket_type).order_by('-created_at')
    return render(request, 'alm/tickets/ticket_list.html', {
        'project': project, 'tickets': tickets, 'current_type': ticket_type
    })


@login_required
def ticket_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    members = project.members.select_related('user').all()
    if request.method == 'POST':
        assigned_id = request.POST.get('assigned_to')
        Ticket.objects.create(
            project=project,
            ticket_type=request.POST['ticket_type'],
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            assigned_to_id=assigned_id if assigned_id else None,
            start_date=request.POST.get('start_date') or None,
            due_date=request.POST.get('due_date') or None,
            created_by=request.user,
        )
        messages.success(request, "Ticket créé.")
        return redirect('ticket_list', project_id=project.id)
    return render(request, 'alm/tickets/ticket_form.html', {
        'project': project, 'members': members, 'title': 'Nouveau ticket'
    })


@login_required
def ticket_detail(request, project_id, ticket_id):
    project = get_object_or_404(Project, id=project_id)
    ticket = get_object_or_404(Ticket, id=ticket_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST' and request.POST.get('transition'):
        new_status = request.POST['transition']
        comment = request.POST.get('comment', '')
        hours = request.POST.get('hours_spent')
        TicketLog.objects.create(
            ticket=ticket,
            user=request.user,
            from_status=ticket.status,
            to_status=new_status,
            comment=comment,
            hours_spent=hours if hours else None,
        )
        ticket.status = new_status
        ticket.save()
        messages.success(request, f"Statut mis à jour : {ticket.get_status_display()}")
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    logs = ticket.logs.select_related('user').all()
    transitions = ticket.get_available_statuses()
    return render(request, 'alm/tickets/ticket_detail.html', {
        'project': project, 'ticket': ticket, 'logs': logs, 'transitions': transitions
    })


@login_required
def ticket_kanban(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    ticket_type = request.GET.get('type', 'incident')
    tickets = project.tickets.filter(ticket_type=ticket_type)
    columns = {}
    for ticket in tickets:
        col = ticket.status
        if col not in columns:
            columns[col] = []
        columns[col].append(ticket)
    return render(request, 'alm/tickets/ticket_kanban.html', {
        'project': project, 'columns': columns, 'current_type': ticket_type
    })


@login_required
def ticket_gantt(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    from datetime import date, timedelta
    ticket_type = request.GET.get('type', '')
    tickets = project.tickets.all()
    if ticket_type:
        tickets = tickets.filter(ticket_type=ticket_type)
    today = date.today()
    events = []
    for t in tickets:
        start = t.start_date or t.created_at.date()
        end = t.due_date or start + timedelta(days=7)
        events.append({'ticket': t, 'start': start, 'end': end})
    return render(request, 'alm/tickets/ticket_gantt.html', {
        'project': project, 'events': events, 'today': today, 'current_type': ticket_type
    })


@login_required
def ticket_export_csv(request, project_id):
    import csv
    from django.http import HttpResponse
    project = get_object_or_404(Project, id=project_id)
    tickets = project.tickets.all()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="tickets_{project.id}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['ID', 'Type', 'Titre', 'Statut', 'Assigné', 'Créé le'])
    for t in tickets:
        writer.writerow([t.get_formatted_number(), t.get_ticket_type_display(), t.title, t.get_status_display(), t.assigned_to, t.created_at])
    return response
