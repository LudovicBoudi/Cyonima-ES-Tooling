from .models import SiteConfig


def site_config(request):
    config = SiteConfig.objects.first()
    return {
        'site_config': config or {'site_name': 'Cyonima-ES-Tools', 'logo': None}
    }
