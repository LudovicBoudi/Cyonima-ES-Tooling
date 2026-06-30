from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Document, DocumentCategory


@login_required
def document_list(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    docs = Document.objects.select_related('category', 'created_by').all()
    if q:
        docs = docs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))
    if cat:
        docs = docs.filter(category_id=cat)
    categories = DocumentCategory.objects.all()
    return render(request, 'ged/document_list.html', {
        'documents': docs, 'categories': categories, 'q': q, 'cat': cat,
    })


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document.objects.select_related('category', 'created_by'), pk=pk)
    categories = DocumentCategory.objects.all()
    tags_list = [t.strip() for t in doc.tags.split(',') if t.strip()] if doc.tags else []
    return render(request, 'ged/document_detail.html', {'doc': doc, 'categories': categories, 'tags_list': tags_list})


@login_required
def document_download(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.download_count += 1
    doc.save(update_fields=['download_count'])
    from django.http import FileResponse
    return FileResponse(doc.file.open('rb'), filename=doc.filename(), as_attachment=True)


@login_required
def document_create(request):
    if request.method == 'POST':
        doc = Document(
            title=request.POST['title'],
            category_id=request.POST.get('category') or None,
            description=request.POST.get('description', ''),
            version=request.POST.get('version', '1.0'),
            tags=request.POST.get('tags', ''),
            created_by=request.user,
        )
        if 'file' in request.FILES:
            doc.file = request.FILES['file']
            doc.save()
            messages.success(request, f'Document "{doc.title}" ajouté.')
            return redirect('ged_document_detail', pk=doc.pk)
        messages.error(request, 'Veuillez sélectionner un fichier.')
    categories = DocumentCategory.objects.all()
    return render(request, 'ged/document_form.html', {'doc': None, 'categories': categories})


@login_required
def document_edit(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        doc.title = request.POST['title']
        doc.category_id = request.POST.get('category') or None
        doc.description = request.POST.get('description', '')
        doc.version = request.POST.get('version', '1.0')
        doc.tags = request.POST.get('tags', '')
        if 'file' in request.FILES:
            doc.file = request.FILES['file']
        doc.save()
        messages.success(request, f'Document "{doc.title}" modifié.')
        return redirect('ged_document_detail', pk=doc.pk)
    categories = DocumentCategory.objects.all()
    return render(request, 'ged/document_form.html', {'doc': doc, 'categories': categories})


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    categories = DocumentCategory.objects.all()
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document supprimé.')
        return redirect('ged_document_list')
    return render(request, 'ged/confirm_delete.html', {'obj': doc, 'categories': categories})
