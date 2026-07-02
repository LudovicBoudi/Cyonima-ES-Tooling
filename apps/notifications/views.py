from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
from apps.notifications.models import Notification, NotificationSetting


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


@login_required
def notification_preferences(request):
    settings_obj, _ = NotificationSetting.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        settings_obj.email_ticket_change = request.POST.get('email_ticket_change') == 'on'
        settings_obj.email_dat_creation = request.POST.get('email_dat_creation') == 'on'
        settings_obj.email_erp_notification = request.POST.get('email_erp_notification') == 'on'
        settings_obj.digest_daily = request.POST.get('digest_daily') == 'on'
        settings_obj.save()
        messages.success(request, 'Préférences de notification mises à jour.')
        return redirect('notification_preferences')
    return render(request, 'notifications/preferences.html', {'settings': settings_obj})
