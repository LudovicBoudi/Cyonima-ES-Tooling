from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import ComexThread, ComexMessage


def can_access(user):
    return hasattr(user, 'profile') and user.profile.can_write_blog('direction')


@login_required
def thread_list(request):
    if not can_access(request.user):
        messages.error(request, "Accès réservé à la direction générale.")
        return redirect('home')
    threads = ComexThread.objects.all()
    return render(request, 'blogs/comex_thread_list.html', {'threads': threads})


@login_required
def thread_detail(request, thread_id):
    if not can_access(request.user):
        messages.error(request, "Accès réservé à la direction générale.")
        return redirect('home')
    thread = get_object_or_404(ComexThread, id=thread_id)
    if request.method == 'POST':
        ComexMessage.objects.create(
            thread=thread,
            content=request.POST['content'],
            created_by=request.user,
        )
        messages.success(request, "Message ajouté.")
        return redirect('comex_thread_detail', thread_id=thread.id)
    return render(request, 'blogs/comex_thread_detail.html', {'thread': thread})


@login_required
def thread_create(request):
    if not can_access(request.user):
        messages.error(request, "Accès réservé à la direction générale.")
        return redirect('home')
    if request.method == 'POST':
        thread = ComexThread.objects.create(
            title=request.POST['title'],
            created_by=request.user,
        )
        ComexMessage.objects.create(
            thread=thread,
            content=request.POST.get('content', ''),
            created_by=request.user,
        )
        messages.success(request, f"Fil {thread.display_id()} créé.")
        return redirect('comex_thread_detail', thread_id=thread.id)
    return render(request, 'blogs/comex_thread_form.html')
