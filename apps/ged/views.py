from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Document, DocumentCategory, DocumentVersion, SharedLink, UserFavorite, CategorySubscription, AuditLog


def _log_audit(request, document, action, details=''):
    AuditLog.objects.create(
        document=document,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR'),
    )


@login_required
def document_list(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    status = request.GET.get('status', '')
    fav = request.GET.get('fav', '')
    docs = Document.objects.select_related('category', 'created_by').filter(deleted_at__isnull=True)
    if fav and request.user.is_authenticated:
        docs = docs.filter(favorited_by__user=request.user)
    if not status:
        docs = docs.exclude(status='archive')
    if q:
        docs = docs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q) | Q(content_text__icontains=q))
    if cat:
        docs = docs.filter(category_id=cat)
    if status:
        docs = docs.filter(status=status)
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = []
    if request.user.is_authenticated:
        subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True))
    return render(request, 'ged/document_list.html', {
        'documents': docs, 'categories': categories, 'q': q, 'cat': cat, 'filter_status': status,
        'subscribed_cat_ids': subscribed_cat_ids,
    })


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document.objects.select_related('category', 'created_by').prefetch_related('shared_links'), pk=pk)
    categories = DocumentCategory.objects.all()
    tags_list = [t.strip() for t in doc.tags.split(',') if t.strip()] if doc.tags else []
    versions = DocumentVersion.objects.filter(document=doc).select_related('uploaded_by').order_by('-uploaded_at')
    audit_logs = AuditLog.objects.filter(document=doc).select_related('user').order_by('-created_at')[:50]
    is_fav = UserFavorite.objects.filter(user=request.user, document=doc).exists() if request.user.is_authenticated else False
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'ged/document_detail.html', {'doc': doc, 'categories': categories, 'tags_list': tags_list, 'versions': versions, 'audit_logs': audit_logs, 'is_fav': is_fav, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def document_download(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.download_count += 1
    doc.save(update_fields=['download_count'])
    _log_audit(request, doc, 'download')
    from django.http import FileResponse
    return FileResponse(doc.file.open('rb'), filename=doc.filename(), as_attachment=True)


@login_required
def document_create(request):
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
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
            _log_audit(request, doc, 'create')
            messages.success(request, f'Document "{doc.title}" ajouté.')
            return redirect('ged_document_detail', pk=doc.pk)
        messages.error(request, 'Veuillez sélectionner un fichier.')
    return render(request, 'ged/document_form.html', {'doc': None, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def toggle_favorite(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    fav = UserFavorite.objects.filter(user=request.user, document=doc).first()
    if fav:
        fav.delete()
        messages.success(request, f'"{doc.title}" retiré des favoris.')
    else:
        UserFavorite.objects.create(user=request.user, document=doc)
        messages.success(request, f'"{doc.title}" ajouté aux favoris.')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def toggle_subscription(request, cat_pk):
    cat = get_object_or_404(DocumentCategory, pk=cat_pk)
    sub = CategorySubscription.objects.filter(user=request.user, category=cat).first()
    if sub:
        sub.delete()
        messages.success(request, f'Abonnement à "{cat.name}" retiré.')
    else:
        CategorySubscription.objects.create(user=request.user, category=cat)
        messages.success(request, f'Abonné à la catégorie "{cat.name}".')
    return redirect('ged_document_list')


@login_required
def favorites_list(request):
    favs = UserFavorite.objects.filter(user=request.user).select_related('document__category').order_by('-created_at')
    return render(request, 'ged/favorites_list.html', {'favorites': favs})


@login_required
def audit_report(request):
    logs = AuditLog.objects.select_related('document__category', 'user').all().order_by('-created_at')
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'ged/audit_report.html', {'logs': logs, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def trash_list(request):
    docs = Document.objects.filter(deleted_at__isnull=False).select_related('category', 'created_by').order_by('-deleted_at')
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'ged/trash_list.html', {'documents': docs, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def document_restore(request, pk):
    doc = get_object_or_404(Document, pk=pk, deleted_at__isnull=False)
    doc.deleted_at = None
    doc.save(update_fields=['deleted_at'])
    _log_audit(request, doc, 'restore')
    messages.success(request, f'"{doc.title}" restauré.')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def document_permanent_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk, deleted_at__isnull=False)
    title = doc.title
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    if request.method == 'POST':
        _log_audit(request, doc, 'permanent_delete')
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, f'"{title}" supprimé définitivement.')
        return redirect('ged_trash_list')
    return render(request, 'ged/confirm_delete.html', {'obj': doc, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids, 'title': 'Supprimer définitivement', 'permanent': True})


@login_required
def document_share(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    days = int(request.POST.get('days', 7))
    from datetime import timedelta
    link = SharedLink.objects.create(
        document=doc,
        expires_at=timezone.now() + timedelta(days=days),
        created_by=request.user,
    )
    _log_audit(request, doc, 'share', f'Partagé pour {days} jours')
    messages.success(request, f'Lien de partage créé (valable {days} jours).')
    return redirect('ged_document_detail', pk=doc.pk)


def shared_document(request, token):
    link = get_object_or_404(SharedLink, token=token, is_active=True)
    if link.is_expired():
        return render(request, 'ged/shared_expired.html', {'link': link})
    doc = link.document
    if request.GET.get('download'):
        doc.download_count += 1
        doc.save(update_fields=['download_count'])
        from django.http import FileResponse
        return FileResponse(doc.file.open('rb'), filename=doc.filename(), as_attachment=True)
    tags_list = [t.strip() for t in doc.tags.split(',') if t.strip()] if doc.tags else []
    return render(request, 'ged/shared_document.html', {'doc': doc, 'tags_list': tags_list, 'link': link})


@login_required
def delete_shared_link(request, pk):
    link = get_object_or_404(SharedLink, pk=pk)
    if request.method == 'POST':
        link.is_active = False
        link.save(update_fields=['is_active'])
        messages.success(request, 'Lien de partage désactivé.')
    return redirect('ged_document_detail', pk=link.document.pk)


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
            old_file = doc.file
            doc.file = request.FILES['file']
            if old_file and old_file.name:
                DocumentVersion.objects.create(
                    document=doc,
                    file=old_file,
                    version_number=doc.version,
                    notes=f'Version précédente avant mise à jour vers v{doc.version}',
                    uploaded_by=request.user,
                )
        doc.save()
        _log_audit(request, doc, 'edit')
        messages.success(request, f'Document "{doc.title}" modifié.')
        return redirect('ged_document_detail', pk=doc.pk)
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'ged/document_form.html', {'doc': doc, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.deleted_at = timezone.now()
    doc.save(update_fields=['deleted_at'])
    _log_audit(request, doc, 'delete')
    messages.success(request, f'"{doc.title}" déplacé dans la corbeille.')
    return redirect('ged_document_list')


@login_required
def category_list(request):
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'ged/category_list.html', {'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def category_create(request):
    if not request.user.is_staff:
        raise PermissionDenied
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#1a3a6b').strip()
        if name:
            DocumentCategory.objects.create(name=name, color=color, created_by=request.user)
            messages.success(request, f'Catégorie "{name}" créée.')
            return redirect('ged_category_list')
        messages.error(request, 'Le nom est requis.')
    return render(request, 'ged/category_form.html', {'title': 'Nouvelle catégorie', 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def category_edit(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    cat = get_object_or_404(DocumentCategory, pk=pk)
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#1a3a6b').strip()
        if name:
            cat.name = name
            cat.color = color
            cat.save()
            messages.success(request, f'Catégorie "{name}" modifiée.')
            return redirect('ged_category_list')
        messages.error(request, 'Le nom est requis.')
    return render(request, 'ged/category_form.html', {'cat': cat, 'title': 'Modifier la catégorie', 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def category_delete(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    cat = get_object_or_404(DocumentCategory, pk=pk)
    categories = DocumentCategory.objects.all()
    subscribed_cat_ids = list(CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)) if request.user.is_authenticated else []
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f'Catégorie "{name}" supprimée.')
        return redirect('ged_category_list')
    return render(request, 'ged/confirm_delete.html', {'obj': cat, 'categories': categories, 'subscribed_cat_ids': subscribed_cat_ids})


@login_required
def version_restore(request, pk):
    version = get_object_or_404(DocumentVersion, pk=pk)
    doc = version.document
    old_file = doc.file
    doc.file = version.file
    doc.version = version.version_number
    if old_file and old_file.name:
        DocumentVersion.objects.create(
            document=doc,
            file=old_file,
            version_number=f'{version.version_number}-avant-restauration',
            notes=f'Version sauvegardée avant restauration de v{version.version_number}',
            uploaded_by=request.user,
        )
    doc.save()
    _log_audit(request, doc, 'version_restore', f'Restauration vers v{version.version_number}')
    messages.success(request, f'Version v{version.version_number} restaurée pour "{doc.title}".')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def document_submit(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if doc.status != 'brouillon':
        messages.error(request, 'Seul un document en brouillon peut être soumis.')
    else:
        doc.status = 'en_relecture'
        doc.save(update_fields=['status'])
        _log_audit(request, doc, 'submit')
        messages.success(request, f'"{doc.title}" soumis en relecture.')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def document_approve(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if doc.status != 'en_relecture':
        messages.error(request, 'Seul un document en relecture peut être approuvé.')
    elif not request.user.is_staff:
        messages.error(request, 'Seul un membre du staff peut approuver un document.')
    else:
        doc.status = 'publie'
        doc.reviewed_by = request.user
        doc.reviewed_at = timezone.now()
        doc.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        _log_audit(request, doc, 'approve')
        messages.success(request, f'"{doc.title}" publié.')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def document_archive(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if doc.status == 'archive':
        messages.error(request, 'Ce document est déjà archivé.')
    else:
        doc.status = 'archive'
        doc.save(update_fields=['status'])
        _log_audit(request, doc, 'archive')
        messages.success(request, f'"{doc.title}" archivé.')
    return redirect('ged_document_detail', pk=doc.pk)


@login_required
def document_unarchive(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if doc.status != 'archive':
        messages.error(request, 'Seul un document archivé peut être désarchivé.')
    else:
        doc.status = 'brouillon'
        doc.save(update_fields=['status'])
        _log_audit(request, doc, 'unarchive')
        messages.success(request, f'"{doc.title}" désarchivé (repasse en brouillon).')
    return redirect('ged_document_detail', pk=doc.pk)
