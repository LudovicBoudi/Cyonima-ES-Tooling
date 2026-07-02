from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import Repository
from . import git_utils
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project


@login_required
def repo_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    repos = project.repositories.all()
    return render(request, 'alm/repositories/repo_list.html', {
        'project': project, 'repos': repos,
    })


@login_required
def repo_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        name = request.POST['name'].strip()
        url = request.POST.get('url', '').strip()
        local_path = request.POST.get('local_path', '').strip()
        branch = request.POST.get('branch', 'main').strip()
        if not name:
            messages.error(request, "Le nom est requis.")
            return render(request, 'alm/repositories/repo_form.html', {'project': project, 'title': 'Nouveau dépôt'})
        if not url and not local_path:
            messages.error(request, "URL distante ou chemin local requis.")
            return render(request, 'alm/repositories/repo_form.html', {'project': project, 'title': 'Nouveau dépôt'})
        repo = Repository.objects.create(
            project=project,
            name=name,
            description=request.POST.get('description', ''),
            url=url,
            local_path=local_path,
            branch=branch,
        )
        if url and not local_path:
            base = f'/home/ludo/repos/{project.id}/{name}'
            repo.local_path = base
            messages.info(request, f"Clonage de {url}…")
            cloned_path, err = git_utils.clone(url, base, branch)
            if err:
                messages.warning(request, f"Le dépôt a été créé mais le clonage a échoué : {err}")
            else:
                messages.success(request, "Dépôt créé et cloné.")
            repo.save()
        else:
            messages.success(request, "Dépôt créé.")
        return redirect('repo_list', project_id=project.id)
    return render(request, 'alm/repositories/repo_form.html', {'project': project, 'title': 'Nouveau dépôt'})


@login_required
def repo_detail(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    valid = repo.is_valid()
    branches_list = []
    tags_list = []
    recent_commits = []
    error = None
    if valid:
        branches_list, err = git_utils.branches(repo.repo_path())
        tags_list, err = git_utils.tags(repo.repo_path())
        recent_commits, err = git_utils.log(repo.repo_path(), max_count=10, branch=repo.branch)
        error = err
    return render(request, 'alm/repositories/repo_detail.html', {
        'project': project, 'repo': repo, 'valid': valid,
        'branches': branches_list, 'tags': tags_list,
        'recent_commits': recent_commits, 'error': error,
    })


@login_required
def repo_delete(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if request.method == 'POST':
        repo.delete()
        messages.success(request, "Dépôt supprimé.")
        return redirect('repo_list', project_id=project.id)
    return render(request, 'alm/repositories/repo_confirm_delete.html', {'project': project, 'repo': repo})


@login_required
def repo_commits(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    branch = request.GET.get('branch', repo.branch)
    path_filter = request.GET.get('path', '')
    commits, err = git_utils.log(repo.repo_path(), max_count=100, branch=branch, path_filter=path_filter)
    branches_list, _ = git_utils.branches(repo.repo_path())
    return render(request, 'alm/repositories/repo_commits.html', {
        'project': project, 'repo': repo, 'commits': commits,
        'current_branch': branch, 'branches': branches_list,
        'path_filter': path_filter, 'error': err,
    })


@login_required
def repo_commit_detail(request, project_id, repo_id, commit_hash):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    commit, err = git_utils.commit_detail(repo.repo_path(), commit_hash)
    return render(request, 'alm/repositories/repo_commit_detail.html', {
        'project': project, 'repo': repo, 'commit': commit, 'error': err,
    })


@login_required
def repo_tree(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    ref = request.GET.get('ref', repo.branch)
    path_val = request.GET.get('path', '')
    items, err = git_utils.tree(repo.repo_path(), treeish=ref, subpath=path_val)
    # Also get current commit info for the ref
    commits, _ = git_utils.log(repo.repo_path(), max_count=1, branch=ref)
    current_commit = commits[0] if commits else None
    # Breadcrumbs
    breadcrumbs = []
    if path_val:
        parts = path_val.split('/')
        for i, p in enumerate(parts):
            breadcrumbs.append({'name': p, 'path': '/'.join(parts[:i+1])})
    branches_list, _ = git_utils.branches(repo.repo_path())
    return render(request, 'alm/repositories/repo_tree.html', {
        'project': project, 'repo': repo, 'items': items,
        'current_ref': ref, 'current_path': path_val,
        'current_commit': current_commit, 'breadcrumbs': breadcrumbs,
        'branches': branches_list, 'error': err,
    })


@login_required
def repo_file(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    ref = request.GET.get('ref', repo.branch)
    path_val = request.GET.get('path', '')
    content, err = git_utils.file_content(repo.repo_path(), ref=ref, filepath=path_val)
    if content is None:
        messages.error(request, f"Impossible de lire le fichier : {err}")
        return redirect('repo_tree', project_id=project.id, repo_id=repo.id)
    # Determine language for syntax highlighting (basic)
    ext = path_val.rsplit('.', 1)[-1] if '.' in path_val else ''
    lang_map = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'html': 'html',
        'css': 'css', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
        'md': 'markdown', 'sh': 'bash', 'sql': 'sql', 'rs': 'rust',
        'go': 'go', 'java': 'java', 'kt': 'kotlin', 'rb': 'ruby',
        'php': 'php', 'c': 'c', 'cpp': 'cpp', 'h': 'c',
        'xml': 'xml', 'toml': 'toml', 'env': 'ini', 'cfg': 'ini',
        'dockerfile': 'dockerfile', 'tf': 'terraform', 'vue': 'vue',
    }
    lang = lang_map.get(ext.lower(), '')
    breadcrumbs = []
    if path_val:
        parts = path_val.split('/')
        for i, p in enumerate(parts):
            breadcrumbs.append({'name': p, 'path': '/'.join(parts[:i+1])})
    return render(request, 'alm/repositories/repo_file.html', {
        'project': project, 'repo': repo, 'content': content,
        'current_ref': ref, 'current_path': path_val,
        'breadcrumbs': breadcrumbs, 'lang': lang,
    })


@login_required
def repo_pull(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    out, err = git_utils.pull(repo.repo_path(), repo.branch)
    if err:
        messages.warning(request, f"Pull : {err}")
    else:
        messages.success(request, "Dépôt mis à jour.")
    return redirect('repo_detail', project_id=project.id, repo_id=repo.id)


@login_required
def repo_contributors(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    valid = repo.is_valid()
    contributors_list = []
    total = 0
    if valid:
        branch = request.GET.get('branch', '')
        contributors_list, err = git_utils.contributors(repo.repo_path(), branch=branch or None)
        for c in contributors_list:
            total += c['count']
    return render(request, 'alm/repositories/repo_contributors.html', {
        'project': project, 'repo': repo, 'valid': valid,
        'contributors': contributors_list, 'total': total,
    })


@login_required
def repo_fetch(request, project_id, repo_id):
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repo_id, project=project)
    if not can_access_project(project, request.user):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    out, err = git_utils.fetch(repo.repo_path())
    if err:
        messages.warning(request, f"Fetch : {err}")
    else:
        messages.success(request, "Dépôt synchronisé (fetch).")
    return redirect('repo_detail', project_id=project.id, repo_id=repo.id)
