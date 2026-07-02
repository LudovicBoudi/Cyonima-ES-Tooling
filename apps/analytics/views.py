from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
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

    daily_counts = (
        qs_30.annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    count_map = {item['day']: item['count'] for item in daily_counts}
    views_by_day = []
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).date()
        views_by_day.append({'date': day.isoformat(), 'count': count_map.get(day, 0)})

    popular_pages = (
        qs_30.values('url')
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
