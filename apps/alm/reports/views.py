from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project
from apps.alm.tickets.models import TicketLog


@login_required
def time_report(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    logs = TicketLog.objects.filter(ticket__project=project).select_related('user', 'ticket')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    user_filter = request.GET.get('user')
    if start_date:
        logs = logs.filter(created_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(created_at__date__lte=end_date)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    total_hours = logs.aggregate(total=Sum('hours_spent'))['total'] or 0
    by_user = logs.values('user__username').annotate(total=Sum('hours_spent')).order_by('-total')
    by_type = logs.values('ticket__ticket_type').annotate(total=Sum('hours_spent')).order_by('-total')
    recent = logs.order_by('-created_at')[:50]
    members = project.members.select_related('user').all()
    return render(request, 'alm/reports/time_report.html', {
        'project': project,
        'total_hours': total_hours,
        'by_user': by_user,
        'by_type': by_type,
        'recent': recent,
        'members': members,
    })
