from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import PageView


@staff_member_required
def dashboard(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    qs_30 = PageView.objects.filter(timestamp__gte=thirty_days_ago)
    qs_7 = PageView.objects.filter(timestamp__gte=seven_days_ago)

    total_views_30 = qs_30.count()
    unique_visitors_30 = qs_30.values('session_key').distinct().count()
    total_views_7 = qs_7.count()
    unique_visitors_7 = qs_7.values('session_key').distinct().count()

    views_by_day = []
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = PageView.objects.filter(
            timestamp__year=day.year,
            timestamp__month=day.month,
            timestamp__day=day.day,
        ).count()
        views_by_day.append({'date': day.isoformat(), 'count': count})

    popular_pages = (
        PageView.objects.filter(timestamp__gte=thirty_days_ago)
        .values('url')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )

    return render(request, 'administration/analytics.html', {
        'total_views_30': total_views_30,
        'unique_visitors_30': unique_visitors_30,
        'total_views_7': total_views_7,
        'unique_visitors_7': unique_visitors_7,
        'views_by_day': views_by_day,
        'popular_pages': popular_pages,
    })
