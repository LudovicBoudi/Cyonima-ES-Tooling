from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Favorite
from .registry import REGISTRY, get_label, get_url, get_module


def _resolve_model(content_type):
    from django.apps import apps
    if content_type not in REGISTRY:
        return None
    parts = content_type.split('.')
    if len(parts) != 2:
        return None
    app_label, model_name = parts
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


@login_required
def toggle_favorite(request):
    if request.method != 'POST':
        return redirect('favorites:list')
    content_type = request.POST.get('content_type', '')
    object_id = request.POST.get('object_id', '')
    if not content_type or not object_id:
        messages.error(request, 'Paramètres invalides.')
        return redirect('favorites:list')
    try:
        object_id = int(object_id)
    except (ValueError, TypeError):
        messages.error(request, 'ID invalide.')
        return redirect('favorites:list')
    fav = Favorite.objects.filter(
        user=request.user, content_type=content_type, object_id=object_id
    ).first()
    if fav:
        fav.delete()
        messages.success(request, 'Retiré des favoris.')
    else:
        model = _resolve_model(content_type)
        if not model:
            messages.error(request, 'Type non supporté.')
            return redirect('favorites:list')
        try:
            obj = model.objects.get(pk=object_id)
        except model.DoesNotExist:
            messages.error(request, 'Objet introuvable.')
            return redirect('favorites:list')
        Favorite.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            label=get_label(obj),
            module=get_module(obj),
            url=get_url(obj),
        )
        messages.success(request, f'"{get_label(obj)}" ajouté aux favoris.')
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('favorites:list')


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    grouped = {}
    for fav in favorites:
        grouped.setdefault(fav.module, []).append(fav)
    total = favorites.count()
    return render(request, 'favorites/favorites_list.html', {
        'grouped': grouped,
        'total': total,
    })


@login_required
def api_check_favorite(request):
    content_type = request.GET.get('content_type', '')
    object_id = request.GET.get('object_id', '')
    is_fav = Favorite.objects.filter(
        user=request.user, content_type=content_type, object_id=object_id
    ).exists()
    return JsonResponse({'is_favorited': is_fav})
