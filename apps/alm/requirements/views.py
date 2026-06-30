from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Requirement, RequirementAttachment
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project


def build_requirement_tree(requirements):
    tree = []
    def add_children(parent, level=0):
        for req in requirements.filter(parent=parent):
            tree.append({'req': req, 'level': level})
            add_children(req, level + 1)
    add_children(None)
    return tree


@login_required
def requirement_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tree = build_requirement_tree(project.requirements.all())
    return render(request, 'alm/requirements/requirement_list.html', {'project': project, 'tree': tree})


@login_required
def requirement_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    folders = project.requirements.filter(category='folder')
    if request.method == 'POST':
        parent_id = request.POST.get('parent')
        Requirement.objects.create(
            project=project,
            parent_id=parent_id if parent_id else None,
            category=request.POST['category'],
            name=request.POST['name'],
            description=request.POST.get('description', ''),
        )
        messages.success(request, "Exigence créée.")
        return redirect('requirement_list', project_id=project.id)
    return render(request, 'alm/requirements/requirement_form.html', {
        'project': project, 'folders': folders, 'title': 'Nouvelle exigence'
    })


@login_required
def requirement_edit(request, project_id, requirement_id):
    project = get_object_or_404(Project, id=project_id)
    req = get_object_or_404(Requirement, id=requirement_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    folders = project.requirements.filter(category='folder').exclude(id=req.id)
    if request.method == 'POST':
        parent_id = request.POST.get('parent')
        req.parent_id = parent_id if parent_id else None
        req.category = request.POST['category']
        req.name = request.POST['name']
        req.description = request.POST.get('description', '')
        req.save()
        messages.success(request, "Exigence modifiée.")
        return redirect('requirement_list', project_id=project.id)
    return render(request, 'alm/requirements/requirement_form.html', {
        'project': project, 'req': req, 'folders': folders, 'title': 'Modifier exigence'
    })


@login_required
def requirement_delete(request, project_id, requirement_id):
    project = get_object_or_404(Project, id=project_id)
    req = get_object_or_404(Requirement, id=requirement_id, project=project)
    if request.method == 'POST':
        req.delete()
        messages.success(request, "Exigence supprimée.")
        return redirect('requirement_list', project_id=project.id)
    return render(request, 'alm/requirements/requirement_confirm_delete.html', {'project': project, 'req': req})


@login_required
def traceability_matrix(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    requirements = project.requirements.exclude(category='folder')
    matrix = []
    for req in requirements:
        tests = req.test_scenarios.all()
        matrix.append({'requirement': req, 'tests': tests, 'test_count': tests.count()})
    return render(request, 'alm/requirements/traceability.html', {'project': project, 'matrix': matrix})
