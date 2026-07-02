from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.utils import timezone
from .models import Project, ProjectMember


def can_access_project(project, user):
    if hasattr(user, 'profile') and user.profile.is_admin():
        return True
    return project.user_is_member(user)


@login_required
def project_list(request):
    projects = Project.objects.filter(
        members__user=request.user
    ).distinct().order_by('-created_at')
    if hasattr(request.user, 'profile') and request.user.profile.is_admin():
        projects = Project.objects.all().order_by('-created_at')
    return render(request, 'alm/projects/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        project = Project.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            created_by=request.user,
        )
        ProjectMember.objects.create(
            project=project,
            user=request.user,
            role='chef_projet',
        )
        messages.success(request, f"Projet '{project.name}' créé.")
        return redirect('project_detail', project_id=project.id)
    return render(request, 'alm/projects/project_form.html', {'title': 'Nouveau projet'})


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé à ce projet.")
        return redirect('project_list')
    stats = {
        'members_count': project.members.count(),
        'requirements_count': project.requirements.count(),
        'tests_count': project.test_scenarios.count(),
        'tickets_count': project.tickets.count(),
    }
    tickets_by_status = project.tickets.values('status').annotate(count=Count('id')).order_by('status')
    tickets_by_type = project.tickets.values('ticket_type').annotate(count=Count('id')).order_by('ticket_type')
    requirements_by_category = project.requirements.values('category').annotate(count=Count('id')).order_by('category')
    recent_tickets = project.tickets.select_related('assigned_to', 'created_by').order_by('-created_at')[:5]
    campaigns = project.campaigns.annotate(test_count=Count('tests')).all()
    today = timezone.now().date()
    upcoming_deadlines = project.tickets.filter(due_date__gte=today, status__in=['nouveau', 'assigne', 'en_cours']).order_by('due_date')[:5]
    from apps.alm.tickets.models import TicketLog
    recent_activity = TicketLog.objects.filter(ticket__project=project).select_related('user', 'ticket').order_by('-created_at')[:10]
    return render(request, 'alm/projects/project_detail.html', {
        'project': project, 'stats': stats,
        'tickets_by_status': list(tickets_by_status),
        'tickets_by_type': list(tickets_by_type),
        'requirements_by_category': list(requirements_by_category),
        'recent_tickets': recent_tickets,
        'campaigns': campaigns,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_activity': recent_activity,
    })


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        project.name = request.POST['name']
        project.description = request.POST.get('description', '')
        project.save()
        messages.success(request, "Projet modifié.")
        return redirect('project_detail', project_id=project.id)
    return render(request, 'alm/projects/project_form.html', {'project': project, 'title': 'Modifier projet'})


@login_required
def member_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    members = project.members.select_related('user').all()
    return render(request, 'alm/projects/member_list.html', {'project': project, 'members': members})


@login_required
def member_add(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=request.POST['username'])
            if project.user_is_member(user):
                messages.error(request, "Cet utilisateur est déjà membre.")
            else:
                ProjectMember.objects.create(
                    project=project,
                    user=user,
                    role=request.POST['role'],
                )
                messages.success(request, f"Membre '{user.username}' ajouté.")
        except User.DoesNotExist:
            messages.error(request, "Utilisateur introuvable.")
        return redirect('member_list', project_id=project.id)
    return render(request, 'alm/projects/member_form.html', {'project': project})


@login_required
def member_remove(request, project_id, member_id):
    project = get_object_or_404(Project, id=project_id)
    member = get_object_or_404(ProjectMember, id=member_id, project=project)
    if request.method == 'POST':
        member.delete()
        messages.success(request, "Membre retiré.")
        return redirect('member_list', project_id=project.id)
    return render(request, 'alm/projects/member_confirm_delete.html', {'project': project, 'member': member})
