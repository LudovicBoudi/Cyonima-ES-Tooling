from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import ActivityReport, AuditLog
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project


@login_required
def journal_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    reports = project.activity_reports.select_related('user').all()
    q_val = request.GET.get('q', '')
    if q_val:
        reports = reports.filter(content__icontains=q_val)
    paginator = Paginator(reports, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'alm/journal/journal_list.html', {
        'project': project, 'reports': page, 'q': q_val,
    })


@login_required
def journal_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        ActivityReport.objects.create(
            project=project,
            user=request.user,
            report_date=request.POST['report_date'],
            content=request.POST['content'],
        )
        messages.success(request, "Compte rendu ajouté.")
        return redirect('journal_list', project_id=project.id)
    return render(request, 'alm/journal/journal_form.html', {'project': project, 'title': 'Nouveau compte rendu'})


@login_required
def audit_log_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    logs = project.audit_logs.select_related('user').all()
    a_val = request.GET.get('action', '')
    e_val = request.GET.get('entity', '')
    if a_val:
        logs = logs.filter(action=a_val)
    if e_val:
        logs = logs.filter(entity_type=e_val)
    paginator = Paginator(logs, 50)
    page = paginator.get_page(request.GET.get('page'))
    entity_types = list(logs.values_list('entity_type', flat=True).distinct().order_by('entity_type'))
    return render(request, 'alm/journal/audit_log_list.html', {
        'project': project, 'logs': page,
        'filter_action': a_val, 'filter_entity': e_val,
        'entity_types': entity_types,
        'actions': AuditLog.ACTION_CHOICES,
    })