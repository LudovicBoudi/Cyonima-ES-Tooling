from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def portal_required(view_func):
    @login_required(login_url='portal:login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('home')
        try:
            portal_user = request.user.portal_profile
        except Exception:
            messages.error(request, 'Compte portail introuvable.')
            return redirect('portal:login')
        if not portal_user.is_active:
            messages.error(request, 'Votre compte a été désactivé. Contactez l\'administrateur.')
            return redirect('portal:login')
        return view_func(request, *args, **kwargs)
    return wrapper
