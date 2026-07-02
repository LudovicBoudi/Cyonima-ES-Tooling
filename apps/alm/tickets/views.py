from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Ticket, TicketLog, Sprint, TicketAttachment, Release
from apps.alm.repositories.models import Repository
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project
from apps.alm.journal.utils import log_audit
from apps.notifications.utils import notify_ticket_assigned, notify_ticket_status_changed


@login_required
def ticket_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    ticket_type = request.GET.get('type', '')
    s_val = request.GET.get('status', '')
    q_val = request.GET.get('q', '')
    a_val = request.GET.get('assigned', '')
    tickets = project.tickets.select_related('assigned_to').all()
    if ticket_type:
        tickets = tickets.filter(ticket_type=ticket_type)
    if s_val:
        tickets = tickets.filter(status=s_val)
    if q_val:
        tickets = tickets.filter(Q(title__icontains=q_val) | Q(description__icontains=q_val) | Q(number__icontains=q_val))
    if a_val:
        tickets = tickets.filter(assigned_to_id=a_val)
    paginator = Paginator(tickets, 25)
    page = paginator.get_page(request.GET.get('page'))
    members = project.members.select_related('user').all()
    status_choices = list(Ticket.objects.filter(project=project).values_list('status', flat=True).distinct().order_by('status'))
    return render(request, 'alm/tickets/ticket_list.html', {
        'project': project, 'tickets': page, 'current_type': ticket_type,
        'filter_status': s_val, 'q': q_val, 'filter_assigned': a_val, 'members': members,
        'status_choices': status_choices,
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
        ticket = Ticket.objects.create(
            project=project,
            ticket_type=request.POST['ticket_type'],
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            assigned_to_id=assigned_id if assigned_id else None,
            start_date=request.POST.get('start_date') or None,
            due_date=request.POST.get('due_date') or None,
            created_by=request.user,
        )
        log_audit(project, request.user, 'create', ticket.get_ticket_type_display(), ticket.id,
                  f"Ticket {ticket.get_formatted_number()} créé : {ticket.title}")
        notify_ticket_assigned(ticket, ticket.assigned_to, request.user)
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
        old_status = ticket.status
        TicketLog.objects.create(
            ticket=ticket,
            user=request.user,
            from_status=old_status,
            to_status=new_status,
            comment=comment,
            hours_spent=hours if hours else None,
        )
        ticket.status = new_status
        if new_status == 'cloture':
            repo_id = request.POST.get('closing_repository')
            commit_hash = request.POST.get('closing_commit_hash', '').strip()
            if commit_hash:
                ticket.closing_commit_hash = commit_hash
                if repo_id:
                    ticket.closing_repository_id = repo_id
        ticket.save()
        log_audit(project, request.user, 'status_change', ticket.get_ticket_type_display(), ticket.id,
                  f"Ticket {ticket.get_formatted_number()} : {old_status} → {new_status}",
                  comment)
        notify_ticket_status_changed(ticket, old_status, new_status, request.user)
        messages.success(request, f"Statut mis à jour : {ticket.get_status_display()}")
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    if request.method == 'POST' and request.POST.get('link_commit'):
        repo_id = request.POST.get('closing_repository')
        commit_hash = request.POST.get('closing_commit_hash', '').strip()
        if commit_hash:
            ticket.closing_commit_hash = commit_hash
            ticket.closing_repository_id = repo_id or None
            ticket.save()
            messages.success(request, "Commit lié au ticket.")
        else:
            messages.error(request, "Hash du commit requis.")
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    if request.method == 'POST' and request.POST.get('unlink_commit'):
        ticket.closing_commit_hash = ''
        ticket.closing_repository = None
        ticket.save()
        messages.success(request, "Lien commit retiré.")
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    if request.method == 'POST' and request.FILES.get('attachment'):
        f = request.FILES['attachment']
        TicketAttachment.objects.create(ticket=ticket, file=f, filename=f.name, uploaded_by=request.user)
        messages.success(request, f'Pièce jointe "{f.name}" ajoutée.')
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    logs = ticket.logs.select_related('user').all()
    transitions = ticket.get_available_statuses()
    repos = project.repositories.all()
    total_hours = ticket.logs.aggregate(total=Sum('hours_spent'))['total'] or 0
    return render(request, 'alm/tickets/ticket_detail.html', {
        'project': project, 'ticket': ticket, 'logs': logs, 'transitions': transitions, 'repos': repos,
        'total_hours': total_hours,
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
def ticket_kanban_update(request, project_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    import json
    data = json.loads(request.body)
    project = get_object_or_404(Project, id=project_id)
    for item in data:
        try:
            ticket = Ticket.objects.get(id=item['id'], project=project)
            old_status = ticket.status
            new_status = item['status']
            if new_status in ticket.get_available_statuses() or True:  # allow any status via kanban
                TicketLog.objects.create(
                    ticket=ticket,
                    user=request.user,
                    from_status=old_status,
                    to_status=new_status,
                )
                ticket.status = new_status
                ticket.save()
                log_audit(project, request.user, 'status_change', ticket.get_ticket_type_display(), ticket.id,
                          f"Ticket {ticket.get_formatted_number()} : {old_status} → {new_status}")
                notify_ticket_status_changed(ticket, old_status, new_status, request.user)
        except Ticket.DoesNotExist:
            continue
    return JsonResponse({'ok': True})


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


@login_required
def ticket_edit(request, project_id, ticket_id):
    project = get_object_or_404(Project, id=project_id)
    ticket = get_object_or_404(Ticket, id=ticket_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    members = project.members.select_related('user').all()
    if request.method == 'POST':
        old_assigned = ticket.assigned_to
        ticket.title = request.POST['title']
        ticket.description = request.POST.get('description', '')
        ticket.assigned_to_id = request.POST.get('assigned_to') or None
        ticket.start_date = request.POST.get('start_date') or None
        ticket.due_date = request.POST.get('due_date') or None
        repo_id = request.POST.get('closing_repository')
        commit_hash = request.POST.get('closing_commit_hash', '').strip()
        if commit_hash:
            ticket.closing_commit_hash = commit_hash
            ticket.closing_repository_id = repo_id or None
        ticket.save()
        log_audit(project, request.user, 'update', ticket.get_ticket_type_display(), ticket.id,
                  f"Ticket {ticket.get_formatted_number()} modifié : {ticket.title}")
        if ticket.assigned_to != old_assigned:
            notify_ticket_assigned(ticket, ticket.assigned_to, request.user)
        messages.success(request, "Ticket modifié.")
        return redirect('ticket_detail', project_id=project.id, ticket_id=ticket.id)
    repos = project.repositories.all()
    return render(request, 'alm/tickets/ticket_form.html', {
        'project': project, 'ticket': ticket, 'members': members, 'title': 'Modifier ticket', 'repos': repos,
    })


@login_required
def sprint_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    sprints = project.sprints.annotate(ticket_count=Count('tickets'), completed_count=Count('tickets', filter=Q(tickets__status='cloture'))).all()
    return render(request, 'alm/tickets/sprint_list.html', {
        'project': project, 'sprints': sprints,
    })


@login_required
def sprint_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        Sprint.objects.create(
            project=project,
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date'],
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, "Sprint créé.")
        return redirect('sprint_list', project_id=project.id)
    return render(request, 'alm/tickets/sprint_form.html', {'project': project, 'title': 'Nouveau sprint'})


@login_required
def sprint_detail(request, project_id, sprint_id):
    project = get_object_or_404(Project, id=project_id)
    sprint = get_object_or_404(Sprint, id=sprint_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tickets_by_status = sprint.tickets.values('status').annotate(count=Count('id')).order_by('status')
    tickets_list = sprint.tickets.select_related('assigned_to').all()
    from django.db.models.functions import TruncDate
    from django.db.models import Count as C
    from datetime import date, timedelta
    burndown = []
    if sprint.end_date and sprint.start_date:
        total_days = (sprint.end_date - sprint.start_date).days
        if total_days > 0:
            day = sprint.start_date
            total = sprint.total_tickets()
            while day <= sprint.end_date:
                remaining = sprint.tickets.exclude(status='cloture', ticketlog__created_at__date__lte=day).count()
                # simpler: count tickets where status is not closed
                done = sprint.tickets.filter(status='cloture', ticketlog__created_at__date__lte=day).count()
                ideal = total - (total / max(total_days, 1)) * (day - sprint.start_date).days
                burndown.append({'date': day.isoformat(), 'remaining': total - done, 'ideal': round(ideal)})
                day += timedelta(days=1)
    return render(request, 'alm/tickets/sprint_detail.html', {
        'project': project, 'sprint': sprint, 'tickets': tickets_list,
        'tickets_by_status': list(tickets_by_status), 'burndown': burndown,
    })


@login_required
def sprint_add_tickets(request, project_id, sprint_id):
    project = get_object_or_404(Project, id=project_id)
    sprint = get_object_or_404(Sprint, id=sprint_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        ticket_ids = request.POST.getlist('tickets')
        sprint.tickets.add(*ticket_ids)
        messages.success(request, "Tickets ajoutés au sprint.")
        return redirect('sprint_detail', project_id=project.id, sprint_id=sprint.id)
    available = project.tickets.exclude(id__in=sprint.tickets.values('id'))
    return render(request, 'alm/tickets/sprint_add_tickets.html', {
        'project': project, 'sprint': sprint, 'available': available,
    })


@login_required
def ticket_import_csv(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST' and request.FILES.get('file'):
        import csv, io
        from datetime import datetime
        file = request.FILES['file']
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        count = 0
        for row in reader:
            title = row.get('titre', row.get('title', '')).strip()
            if not title:
                continue
            ttype = row.get('type', 'tache').strip().lower()
            if ttype not in dict(Ticket.TICKET_TYPES):
                ttype = 'tache'
            assigned = None
            username = row.get('assigne', row.get('assigned_to', '')).strip()
            if username:
                assigned = User.objects.filter(username=username).first()
            due = row.get('echeance', row.get('due_date', '')).strip()
            due_date = None
            if due:
                try:
                    due_date = datetime.strptime(due[:10], '%Y-%m-%d').date()
                except ValueError:
                    pass
            Ticket.objects.create(
                project=project,
                ticket_type=ttype,
                title=title,
                description=row.get('description', ''),
                assigned_to=assigned,
                due_date=due_date,
                created_by=request.user,
            )
            count += 1
        messages.success(request, f"{count} ticket(s) importé(s).")
        return redirect('ticket_list', project_id=project.id)
    return render(request, 'alm/tickets/ticket_import.html', {'project': project})


@login_required
def release_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    releases = project.releases.annotate(
        ticket_count=Count('tickets'),
        completed_count=Count('tickets', filter=Q(tickets__status='cloture'))
    ).all()
    return render(request, 'alm/tickets/release_list.html', {'project': project, 'releases': releases})


@login_required
def release_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        r = Release.objects.create(
            project=project,
            name=request.POST['name'],
            version=request.POST.get('version', ''),
            description=request.POST.get('description', ''),
            release_date=request.POST.get('release_date') or None,
            is_released=request.POST.get('is_released') == 'on',
        )
        messages.success(request, f"Release {r} créée.")
        return redirect('release_list', project_id=project.id)
    return render(request, 'alm/tickets/release_form.html', {'project': project, 'title': 'Nouvelle release'})


@login_required
def release_detail(request, project_id, release_id):
    project = get_object_or_404(Project, id=project_id)
    release_obj = get_object_or_404(Release, id=release_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tickets = release_obj.tickets.select_related('assigned_to').all()
    available = project.tickets.exclude(id__in=release_obj.tickets.values('id'))
    return render(request, 'alm/tickets/release_detail.html', {
        'project': project, 'release': release_obj, 'tickets': tickets, 'available': available,
    })


@login_required
def release_add_tickets(request, project_id, release_id):
    project = get_object_or_404(Project, id=project_id)
    release_obj = get_object_or_404(Release, id=release_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        ticket_ids = request.POST.getlist('tickets')
        release_obj.tickets.add(*ticket_ids)
        messages.success(request, "Tickets ajoutés à la release.")
        return redirect('release_detail', project_id=project.id, release_id=release_obj.id)
    return redirect('release_detail', project_id=project.id, release_id=release_obj.id)
