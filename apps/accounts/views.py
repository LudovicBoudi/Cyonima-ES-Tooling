from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserCreateForm


@staff_member_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur '{user.username}' créé avec succès.")
            return redirect('home')
    else:
        form = UserCreateForm()
    return render(request, 'registration/user_create.html', {'form': form})
