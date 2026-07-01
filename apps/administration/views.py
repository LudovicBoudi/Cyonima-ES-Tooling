from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from apps.accounts.models import UserProfile, Role
from apps.accounts.forms import UserCreateForm
from apps.core.models import SiteConfig
from apps.budget.providers.models import Provider
from apps.budget.budgets.models import BudgetYear
from apps.budget.dat.models import DAT
from apps.budget.todo.models import TodoItem
from django.http import HttpResponse
from django.conf import settings
import os
import zipfile
import io
from datetime import datetime


def admin_required(view_func):
    decorated_view = login_required(staff_member_required(view_func))
    return decorated_view


@admin_required
def dashboard(request):
    context = {
        'users_count': User.objects.count(),
        'providers_count': Provider.objects.count(),
        'budgets_count': BudgetYear.objects.count(),
        'dat_count': DAT.objects.count(),
        'todo_count': TodoItem.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_dats': DAT.objects.order_by('-created_at')[:5],
    }
    return render(request, 'administration/dashboard.html', context)


@admin_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'administration/user_list.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur '{user.username}' créé.")
            return redirect('admin_user_list')
    else:
        form = UserCreateForm()
    return render(request, 'administration/user_form.html', {'form': form, 'title': 'Créer un utilisateur'})


@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role_ids = request.POST.getlist('roles')
        is_active = request.POST.get('is_active') == 'on'

        if username:
            user.username = username
        user.email = email
        user.is_active = is_active
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.roles.set(role_ids)

        messages.success(request, f"Utilisateur '{user.username}' modifié.")
        return redirect('admin_user_list')
    roles = Role.objects.all()
    return render(request, 'administration/user_edit.html', {'edit_user': user, 'all_roles': roles})


@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"Utilisateur '{username}' supprimé.")
        return redirect('admin_user_list')
    return render(request, 'administration/user_confirm_delete.html', {'edit_user': user})


@admin_required
def site_config_view(request):
    config = SiteConfig.objects.first()
    if not config:
        config = SiteConfig.objects.create()

    if request.method == 'POST':
        config.site_name = request.POST.get('site_name', 'Cyonima-ES-Tools')
        if 'logo' in request.FILES:
            config.logo = request.FILES['logo']
        config.save()
        messages.success(request, 'Configuration mise à jour.')
        return redirect('admin_site_config')

    return render(request, 'administration/site_config.html', {'config': config})


@admin_required
def provider_list(request):
    return redirect('provider_list')


@admin_required
def provider_create(request):
    return redirect('provider_create')


@admin_required
def provider_edit(request, pk):
    return redirect('provider_edit', pk=pk)


@admin_required
def provider_delete(request, pk):
    return redirect('provider_delete', pk=pk)


@admin_required
def budget_list(request):
    return redirect('budget_list')


@admin_required
def budget_create(request):
    return redirect('budget_create')


@admin_required
def budget_edit(request, pk):
    return redirect('budget_edit', pk=pk)


@admin_required
def budget_delete(request, pk):
    return redirect('budget_delete', pk=pk)


@admin_required
def backup(request):
    if request.method == 'POST' and request.FILES.get('backup_file'):
        import json
        from io import BytesIO
        from django.core.management import call_command

        backup_file = request.FILES['backup_file']
        try:
            with zipfile.ZipFile(backup_file) as zf:
                if 'db.json' not in zf.namelist():
                    messages.error(request, "Fichier de sauvegarde invalide : db.json introuvable.")
                    return redirect('admin_backup')

                db_data = zf.read('db.json').decode('utf-8')

                call_command('flush', interactive=False, verbosity=0)

                from io import StringIO
                call_command('loaddata', stdin=StringIO(db_data), verbosity=0, format='json')

                if os.path.isdir(settings.MEDIA_ROOT):
                    import shutil
                    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                        for f in files:
                            os.remove(os.path.join(root, f))

                    for item in zf.namelist():
                        if item.startswith('media/') and not item.endswith('/'):
                            zf.extract(item, settings.BASE_DIR)

                messages.success(request, "Sauvegarde restaurée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la restauration : {e}")
        return redirect('admin_backup')

    elif request.method == 'POST':
        from io import BytesIO
        from django.core.management import call_command
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('version.txt', f"Sauvegarde Cyonima-ES-Tools - {datetime.now().isoformat()}\n")

            out = io.StringIO()
            call_command('dumpdata', stdout=out, exclude=['contenttypes', 'sessions', 'admin'])
            zf.writestr('db.json', out.getvalue())

            if os.path.isdir(settings.MEDIA_ROOT):
                for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                    for f in files:
                        path = os.path.join(root, f)
                        zf.write(path, f'media/{os.path.relpath(path, settings.MEDIA_ROOT)}')

        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="cyonima_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        return response
    return render(request, 'administration/backup.html')
