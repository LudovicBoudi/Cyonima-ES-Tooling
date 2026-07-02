import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import TodoItem


@login_required
def todo_kanban(request):
    items = TodoItem.objects.all()
    columns = [
        {'status': 'todo', 'items': items.filter(status='todo')},
        {'status': 'in_progress', 'items': items.filter(status='in_progress')},
        {'status': 'done', 'items': items.filter(status='done')},
    ]
    return render(request, 'budget/todo_kanban.html', {'columns': columns})


@login_required
def todo_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        deadline = request.POST.get('deadline', '')
        if title and deadline:
            TodoItem.objects.create(title=title, deadline=deadline, status=request.POST.get('status', 'todo'))
            messages.success(request, 'Tâche ajoutée.')
        else:
            messages.error(request, 'Titre et date limite requis.')
    return redirect('todo_kanban')


@login_required
def todo_delete(request, pk):
    item = get_object_or_404(TodoItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Tâche supprimée.')
    return redirect('todo_kanban')


@login_required
def todo_update_status(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(TodoItem, pk=pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'JSON invalide'}, status=400)
        new_status = data.get('status')
        if new_status in dict(TodoItem.STATUS_CHOICES):
            item.status = new_status
            item.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'Statut invalide'}, status=400)
    return JsonResponse({'ok': False}, status=405)
