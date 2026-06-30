from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import ActivityReport
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project


@login_required
def journal_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    reports = project.activity_reports.select_related('user').all()
    return render(request, 'alm/journal/journal_list.html', {'project': project, 'reports': reports})


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
