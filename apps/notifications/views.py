from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.decorators.http import require_POST
from apps.notifications.models import Notification


@login_required
def notification_list(request):
    q = request.GET.get('q', '')
    notifs = Notification.objects.filter(user=request.user)
    if q:
        notifs = notifs.filter(Q(title__icontains=q) | Q(message__icontains=q))
    if request.method == 'POST' and request.POST.get('mark_read'):
        notifs.filter(is_read=False).update(is_read=True)
        return redirect('notification_list')
    return render(request, 'notifications/list.html', {
        'notifications': notifs,
        'unread_count': notifs.filter(is_read=False).count(),
        'q': q,
    })
