from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
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
    q_val = request.GET.get('q', '')
    c_val = request.GET.get('category', '')
    reqs = project.requirements.all()
    if q_val:
        reqs = reqs.filter(Q(name__icontains=q_val) | Q(description__icontains=q_val) | Q(number__icontains=q_val))
    if c_val:
        reqs = reqs.filter(category=c_val)
    tree = build_requirement_tree(reqs)
    folders = project.requirements.filter(category='folder')
    return render(request, 'alm/requirements/requirement_list.html', {
        'project': project, 'tree': tree, 'q': q_val, 'filter_category': c_val,
        'categories': Requirement.CATEGORY_CHOICES, 'folders': folders,
    })


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


@login_required
def requirement_export_csv(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    import csv
    from django.http import HttpResponse
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="exigences_{project.id}.csv"'
    resp.write('\ufeff')
    w = csv.writer(resp)
    w.writerow(['N°', 'Catégorie', 'Nom', 'Description', 'Parent'])
    for req in project.requirements.all().order_by('number'):
        w.writerow([req.get_formatted_number(), req.get_category_display(), req.name, req.description, req.parent.get_formatted_number() if req.parent else ''])
    return resp


@login_required
def folder_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    if request.method == 'POST':
        parent_id = request.POST.get('parent')
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'Le nom est requis'}, status=400)
        Requirement.objects.create(
            project=project,
            parent_id=parent_id if parent_id else None,
            category='folder',
            name=name,
        )
        messages.success(request, "Dossier créé.")
        return redirect('requirement_list', project_id=project.id)
    return redirect('requirement_list', project_id=project.id)


@login_required
def requirement_detail(request, project_id, requirement_id):
    project = get_object_or_404(Project, id=project_id)
    req = get_object_or_404(Requirement, id=requirement_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tests = req.test_scenarios.all()
    folders = project.requirements.filter(category='folder').exclude(id=req.id)
    if request.method == 'POST':
        if request.FILES.get('file'):
            f = request.FILES['file']
            RequirementAttachment.objects.create(
                requirement=req,
                file=f,
                filename=f.name,
                uploaded_by=request.user,
            )
            messages.success(request, "Pièce jointe ajoutée.")
        return redirect('requirement_detail', project_id=project.id, requirement_id=req.id)
    return render(request, 'alm/requirements/requirement_detail.html', {
        'project': project, 'req': req, 'tests': tests, 'folders': folders,
    })


@login_required
def requirement_import_csv(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST' and request.FILES.get('file'):
        import csv, io
        file = request.FILES['file']
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        count = 0
        for row in reader:
            name = row.get('nom', row.get('name', '')).strip()
            if not name:
                continue
            category = row.get('categorie', row.get('category', 'logiciel')).strip()
            if category not in dict(Requirement.CATEGORY_CHOICES):
                category = 'logiciel'
            parent_ref = row.get('parent', '').strip()
            parent = None
            if parent_ref:
                try:
                    parent_num = int(parent_ref.replace('D-', '').replace('-', '').lstrip('0'))
                    parent = Requirement.objects.filter(project=project, number=parent_num, category='folder').first()
                except ValueError:
                    pass
            Requirement.objects.create(
                project=project,
                parent=parent,
                category=category,
                name=name,
                description=row.get('description', ''),
            )
            count += 1
        messages.success(request, f"{count} exigence(s) importée(s).")
        return redirect('requirement_list', project_id=project.id)
    return render(request, 'alm/requirements/requirement_import.html', {'project': project})
