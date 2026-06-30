from django.urls import resolve, Resolver404
from .models import PageView


class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code != 200:
            return response

        try:
            resolved = resolve(request.path_info)
            url_name = resolved.url_name
        except Resolver404:
            return response

        exclude_names = {'admin_dashboard', 'admin_user_list', 'admin_user_create',
                         'admin_user_edit', 'admin_user_delete', 'admin_site_config',
                         'admin_backup', 'admin_analytics'}
        if url_name in exclude_names:
            return response

        exclude_prefixes = ('/admin/', '/static/', '/media/')
        if any(request.path_info.startswith(p) for p in exclude_prefixes):
            return response

        if request.path_info == '/':
            return response

        user = request.user if request.user.is_authenticated else None

        PageView.objects.create(
            url=request.path_info,
            user=user,
            session_key=request.session.session_key or '',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
