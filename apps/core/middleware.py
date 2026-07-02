from django.http import HttpResponsePermanentRedirect
from django.conf import settings
from apps.core.models import SiteConfig


class HttpsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._config = None
        self._last_check = 0

    def _get_config(self):
        import time
        now = time.time()
        if now - self._last_check > 300:
            try:
                self._config = SiteConfig.objects.first()
            except Exception:
                self._config = None
            self._last_check = now
        return self._config

    def __call__(self, request):
        config = self._get_config()
        if config and config.https_enabled and not request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            url = url.replace('http://', 'https://', 1)
            return HttpResponsePermanentRedirect(url)
        response = self.get_response(request)
        if config and config.https_enabled and config.hsts_seconds > 0 and request.is_secure():
            response['Strict-Transport-Security'] = f'max-age={config.hsts_seconds}'
        return response
