from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Company, Contact, Deal, Interaction, CrmTask, DealStageLog, CrmAttachment
from django.utils.dateparse import parse_datetime
import json, csv
from django.http import HttpResponse


def _can_access(user):
    return True


@login_required
def dashboard(request):
    total_companies = Company.objects.count()
    total_contacts = Contact.objects.count()
    total_deals = Deal.objects.count()
    total_interactions = Interaction.objects.count()
    total_tasks = CrmTask.objects.count()
    active_deals = Deal.objects.exclude(stage__in=['gagne', 'perdu']).count()
    pipeline_value = Deal.objects.filter(~Q(stage='perdu')).aggregate(Sum('amount'))['amount__sum'] or 0

    deals_by_stage = []
    for code, label in Deal.STAGE_CHOICES:
        deals_by_stage.append({
            'code': code,
            'label': label,
            'count': Deal.objects.filter(stage=code).count(),
        })

    stage_order = ['prospection', 'devis', 'negociation', 'gagne', 'perdu']
    deals_by_stage_sorted = sorted(deals_by_stage, key=lambda x: stage_order.index(x['code']))

    stage_amounts = []
    for code, label in Deal.STAGE_CHOICES:
        total = Deal.objects.filter(stage=code).aggregate(Sum('amount'))['amount__sum'] or 0
        stage_amounts.append({'label': label, 'amount': total})

    won_count = Deal.objects.filter(stage='gagne').count()
    lost_count = Deal.objects.filter(stage='perdu').count()
    total_closed = won_count + lost_count
    conversion_rate = round(won_count / total_closed * 100, 1) if total_closed > 0 else 0

    won_amount = Deal.objects.filter(stage='gagne').aggregate(Sum('amount'))['amount__sum'] or 0
    lost_amount = Deal.objects.filter(stage='perdu').aggregate(Sum('amount'))['amount__sum'] or 0

    deals_by_month = (
        Deal.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'), amount=Sum('amount'))
        .order_by('month')
    )
    month_labels = [d['month'].strftime('%b %Y') if d['month'] else '' for d in deals_by_month]
    month_counts = [d['total'] for d in deals_by_month]
    month_amounts = [float(d['amount'] or 0) for d in deals_by_month]

    top_deals = Deal.objects.filter(~Q(stage='perdu')).order_by('-amount')[:5]

    recent_interactions = Interaction.objects.select_related('contact', 'created_by').order_by('-created_at')[:10]

    upcoming_tasks = CrmTask.objects.filter(completed=False).order_by('due_date', '-created_at')[:10]

    overdue_tasks_count = CrmTask.objects.filter(completed=False, due_date__lt=timezone.now().date()).count()

    return render(request, 'crm/dashboard.html', {
        'total_companies': total_companies,
        'total_contacts': total_contacts,
        'total_deals': total_deals,
        'total_interactions': total_interactions,
        'total_tasks': total_tasks,
        'active_deals': active_deals,
        'pipeline_value': pipeline_value,
        'deals_by_stage': deals_by_stage_sorted,
        'stage_amounts': stage_amounts,
        'won_amount': won_amount,
        'lost_amount': lost_amount,
        'won_count': won_count,
        'lost_count': lost_count,
        'conversion_rate': conversion_rate,
        'deals_by_month': deals_by_month,
        'month_labels': month_labels,
        'month_counts': month_counts,
        'month_amounts': month_amounts,
        'top_deals': top_deals,
        'recent_interactions': recent_interactions,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks_count': overdue_tasks_count,
        'today': timezone.localdate(),
    })


@login_required
def company_list(request):
    companies = Company.objects.annotate(contact_count=Count('contacts'), deal_count=Count('deals'))
    q = request.GET.get('q', '')
    if q:
        companies = companies.filter(Q(name__icontains=q) | Q(sector__icontains=q) | Q(city__icontains=q) | Q(email__icontains=q))
    return render(request, 'crm/company_list.html', {'companies': companies, 'q': q})


@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    contacts = company.contacts.all()
    deals = company.deals.all()
    contact_ids = contacts.values_list('pk', flat=True)
    deal_ids = deals.values_list('pk', flat=True)
    interactions = Interaction.objects.filter(
        Q(contact_id__in=contact_ids) | Q(deal_id__in=deal_ids)
    ).select_related('contact', 'deal', 'created_by').order_by('-created_at')[:30]
    tasks = CrmTask.objects.filter(
        Q(contact_id__in=contact_ids) | Q(deal_id__in=deal_ids)
    ).select_related('contact', 'deal', 'assigned_to').order_by('due_date')[:20]
    return render(request, 'crm/company_detail.html', {
        'company': company, 'contacts': contacts, 'deals': deals,
        'timeline_interactions': interactions, 'timeline_tasks': tasks,
    })


@login_required
def company_create(request):
    if request.method == 'POST':
        company = Company.objects.create(
            name=request.POST['name'],
            sector=request.POST.get('sector', ''),
            address=request.POST.get('address', ''),
            postal_code=request.POST.get('postal_code', ''),
            city=request.POST.get('city', ''),
            country=request.POST.get('country', 'France'),
            website=request.POST.get('website', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            siret=request.POST.get('siret', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Société "{company.name}" créée.')
        return redirect('crm_company_detail', pk=company.pk)
    return render(request, 'crm/company_form.html', {'title': 'Nouvelle société'})


@login_required
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        for field in ['name', 'sector', 'address', 'postal_code', 'city', 'country',
                       'website', 'phone', 'email', 'siret', 'notes']:
            setattr(company, field, request.POST.get(field, ''))
        company.save()
        messages.success(request, f'Société "{company.name}" modifiée.')
        return redirect('crm_company_detail', pk=company.pk)
    return render(request, 'crm/company_form.html', {'company': company, 'title': 'Modifier la société'})


@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        name = company.name
        company.delete()
        messages.success(request, f'Société "{name}" supprimée.')
        return redirect('crm_company_list')
    return render(request, 'crm/company_confirm_delete.html', {'company': company})


@login_required
def contact_list(request):
    contacts = Contact.objects.select_related('company').all()
    q = request.GET.get('q', '')
    company = request.GET.get('company', '')
    if q:
        contacts = contacts.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if company:
        contacts = contacts.filter(company_id=company)
    return render(request, 'crm/contact_list.html', {
        'contacts': contacts, 'q': q, 'filter_company': company,
        'all_companies': Company.objects.all(),
    })


@login_required
def contact_create(request):
    if request.method == 'POST':
        company_pk = request.POST.get('company')
        contact = Contact.objects.create(
            company_id=company_pk if company_pk else None,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            mobile=request.POST.get('mobile', ''),
            function=request.POST.get('function', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Contact "{contact}" créé.')
        return redirect('crm_contact_list')
    companies = Company.objects.all()
    return render(request, 'crm/contact_form.html', {'companies': companies, 'title': 'Nouveau contact'})


@login_required
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        company_pk = request.POST.get('company')
        contact.company_id = company_pk if company_pk else None
        contact.first_name = request.POST['first_name']
        contact.last_name = request.POST['last_name']
        contact.email = request.POST.get('email', '')
        contact.phone = request.POST.get('phone', '')
        contact.mobile = request.POST.get('mobile', '')
        contact.function = request.POST.get('function', '')
        contact.notes = request.POST.get('notes', '')
        contact.save()
        messages.success(request, f'Contact "{contact}" modifié.')
        return redirect('crm_contact_list')
    companies = Company.objects.all()
    return render(request, 'crm/contact_form.html', {
        'contact': contact, 'companies': companies, 'title': 'Modifier le contact',
    })


@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        name = str(contact)
        contact.delete()
        messages.success(request, f'Contact "{name}" supprimé.')
        return redirect('crm_contact_list')
    return render(request, 'crm/contact_confirm_delete.html', {'contact': contact})


@login_required
def deal_list(request):
    deals = Deal.objects.select_related('company', 'contact', 'created_by').all()
    q = request.GET.get('q', '')
    stage = request.GET.get('stage', '')
    company = request.GET.get('company', '')
    if q:
        deals = deals.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if stage:
        deals = deals.filter(stage=stage)
    if company:
        deals = deals.filter(company_id=company)
    return render(request, 'crm/deal_list.html', {
        'deals': deals, 'q': q, 'filter_stage': stage, 'filter_company': company,
        'all_companies': Company.objects.all(),
        'stage_choices': Deal.STAGE_CHOICES,
    })


@login_required
def deal_create(request):
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        deal = Deal.objects.create(
            title=request.POST['title'],
            company_id=request.POST.get('company') or None,
            contact_id=contact_pk if contact_pk else None,
            amount=request.POST.get('amount', 0),
            probability=request.POST.get('probability', 0),
            stage=request.POST.get('stage', 'prospection'),
            expected_close_date=request.POST.get('expected_close_date') or None,
            description=request.POST.get('description', ''),
            created_by=request.user,
        )
        DealStageLog.objects.create(deal=deal, from_stage='', to_stage=deal.stage, changed_by=request.user)
        messages.success(request, f'Affaire "{deal.title}" créée.')
        return redirect('crm_deal_list')
    companies = Company.objects.all()
    contacts = Contact.objects.all()
    return render(request, 'crm/deal_form.html', {
        'companies': companies, 'contacts': contacts, 'title': 'Nouvelle affaire',
        'stage_choices': Deal.STAGE_CHOICES,
    })


@login_required
def deal_edit(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        old_stage = deal.stage
        deal.title = request.POST['title']
        deal.company_id = request.POST.get('company') or None
        deal.contact_id = contact_pk if contact_pk else None
        deal.amount = request.POST.get('amount', 0)
        deal.probability = request.POST.get('probability', 0)
        deal.stage = request.POST.get('stage', 'prospection')
        deal.expected_close_date = request.POST.get('expected_close_date') or None
        deal.description = request.POST.get('description', '')
        deal.save()
        if old_stage != deal.stage:
            DealStageLog.objects.create(deal=deal, from_stage=old_stage, to_stage=deal.stage, changed_by=request.user)
        messages.success(request, f'Affaire "{deal.title}" modifiée.')
        return redirect('crm_deal_list')
    companies = Company.objects.all()
    contacts = Contact.objects.all()
    return render(request, 'crm/deal_form.html', {
        'deal': deal, 'companies': companies, 'contacts': contacts, 'title': 'Modifier l\'affaire',
        'stage_choices': Deal.STAGE_CHOICES,
    })


@login_required
def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        title = deal.title
        deal.delete()
        messages.success(request, f'Affaire "{title}" supprimée.')
        return redirect('crm_deal_list')
    return render(request, 'crm/deal_confirm_delete.html', {'deal': deal})


@login_required
def deal_kanban(request):
    deals = Deal.objects.select_related('company', 'contact', 'created_by').all()
    columns = []
    for code, label in Deal.STAGE_CHOICES:
        columns.append({
            'code': code,
            'label': label,
            'deals': deals.filter(stage=code),
        })
    return render(request, 'crm/deal_kanban.html', {
        'columns': columns,
    })


@login_required
def deal_detail(request, pk):
    deal = get_object_or_404(Deal.objects.select_related('company', 'contact', 'created_by'), pk=pk)
    interactions = Interaction.objects.filter(deal=deal).select_related('contact', 'created_by').order_by('-created_at')
    tasks = CrmTask.objects.filter(deal=deal).select_related('contact', 'assigned_to').order_by('due_date')
    stage_logs = DealStageLog.objects.filter(deal=deal).select_related('changed_by').order_by('-changed_at')
    attachments = CrmAttachment.objects.filter(deal=deal).select_related('uploaded_by').order_by('-uploaded_at')
    return render(request, 'crm/deal_detail.html', {
        'deal': deal, 'interactions': interactions, 'tasks': tasks, 'stage_logs': stage_logs, 'attachments': attachments,
    })


@login_required
def deal_update_stage(request, pk):
    if request.method == 'POST':
        deal = get_object_or_404(Deal, pk=pk)
        data = json.loads(request.body)
        new_stage = data.get('stage')
        valid_stages = [c for c, _ in Deal.STAGE_CHOICES]
        if new_stage in valid_stages:
            old_stage = deal.stage
            if old_stage != new_stage:
                deal.stage = new_stage
                deal.save()
                DealStageLog.objects.create(
                    deal=deal,
                    from_stage=old_stage,
                    to_stage=new_stage,
                    changed_by=request.user,
                )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'Étape invalide'}, status=400)
    return JsonResponse({'ok': False}, status=405)


@login_required
def interaction_list(request):
    contact_pk = request.GET.get('contact')
    deal_pk = request.GET.get('deal')
    type_filter = request.GET.get('type', '')
    q = request.GET.get('q', '')
    interactions = Interaction.objects.select_related('contact', 'deal', 'created_by').all()
    if q:
        interactions = interactions.filter(Q(subject__icontains=q) | Q(content__icontains=q))
    if contact_pk:
        interactions = interactions.filter(contact_id=contact_pk)
    if deal_pk:
        interactions = interactions.filter(deal_id=deal_pk)
    if type_filter:
        interactions = interactions.filter(type=type_filter)
    return render(request, 'crm/interaction_list.html', {
        'interactions': interactions,
        'contacts': Contact.objects.all(),
        'deals': Deal.objects.all(),
        'filter_contact': contact_pk,
        'filter_deal': deal_pk,
        'filter_type': type_filter,
        'q': q,
        'type_choices': Interaction.TYPE_CHOICES,
    })


@login_required
def interaction_create(request):
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        deal_pk = request.POST.get('deal')
        interaction = Interaction.objects.create(
            contact_id=contact_pk,
            deal_id=deal_pk if deal_pk else None,
            type=request.POST.get('type', 'note'),
            subject=request.POST['subject'],
            content=request.POST.get('content', ''),
            created_by=request.user,
        )
        messages.success(request, 'Interaction enregistrée.')
        return redirect('crm_interaction_list')
    contacts = Contact.objects.all()
    deals = Deal.objects.all()
    return render(request, 'crm/interaction_form.html', {
        'contacts': contacts, 'deals': deals, 'title': 'Nouvelle interaction',
        'type_choices': Interaction.TYPE_CHOICES,
    })


@login_required
def interaction_edit(request, pk):
    interaction = get_object_or_404(Interaction, pk=pk)
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        interaction.contact_id = contact_pk
        interaction.deal_id = request.POST.get('deal') or None
        interaction.type = request.POST.get('type', 'note')
        interaction.subject = request.POST['subject']
        interaction.content = request.POST.get('content', '')
        interaction.save()
        messages.success(request, 'Interaction modifiée.')
        return redirect('crm_interaction_list')
    contacts = Contact.objects.all()
    deals = Deal.objects.all()
    return render(request, 'crm/interaction_form.html', {
        'interaction': interaction, 'contacts': contacts, 'deals': deals, 'title': 'Modifier l\'interaction',
        'type_choices': Interaction.TYPE_CHOICES,
    })


@login_required
def interaction_delete(request, pk):
    interaction = get_object_or_404(Interaction, pk=pk)
    if request.method == 'POST':
        interaction.delete()
        messages.success(request, 'Interaction supprimée.')
        return redirect('crm_interaction_list')
    return render(request, 'crm/interaction_confirm_delete.html', {'interaction': interaction})


@login_required
def task_list(request):
    tasks = CrmTask.objects.select_related('contact', 'deal', 'assigned_to').all()
    q = request.GET.get('q', '')
    completed = request.GET.get('completed', '')
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if completed == '1':
        tasks = tasks.filter(completed=True)
    elif completed == '0':
        tasks = tasks.filter(completed=False)
    return render(request, 'crm/task_list.html', {'tasks': tasks, 'q': q, 'filter_completed': completed, 'today': timezone.localdate()})


@login_required
def task_create(request):
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        deal_pk = request.POST.get('deal')
        task = CrmTask.objects.create(
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            due_date=request.POST.get('due_date') or None,
            completed=request.POST.get('completed') == 'on',
            contact_id=contact_pk if contact_pk else None,
            deal_id=deal_pk if deal_pk else None,
            assigned_to_id=request.POST.get('assigned_to') or None,
            reminder_date=parse_datetime(request.POST['reminder_date']) if request.POST.get('reminder_date') else None,
            created_by=request.user,
        )
        messages.success(request, f'Tâche "{task.title}" créée.')
        return redirect('crm_task_list')
    users = User.objects.all()
    contacts = Contact.objects.all()
    deals = Deal.objects.all()
    return render(request, 'crm/task_form.html', {
        'contacts': contacts, 'deals': deals, 'users': users, 'title': 'Nouvelle tâche',
    })


@login_required
def task_edit(request, pk):
    task = get_object_or_404(CrmTask, pk=pk)
    if request.method == 'POST':
        contact_pk = request.POST.get('contact')
        deal_pk = request.POST.get('deal')
        task.title = request.POST['title']
        task.description = request.POST.get('description', '')
        task.due_date = request.POST.get('due_date') or None
        task.completed = request.POST.get('completed') == 'on'
        task.contact_id = contact_pk if contact_pk else None
        task.deal_id = deal_pk if deal_pk else None
        task.assigned_to_id = request.POST.get('assigned_to') or None
        task.reminder_date = parse_datetime(request.POST['reminder_date']) if request.POST.get('reminder_date') else None
        task.save()
        messages.success(request, f'Tâche "{task.title}" modifiée.')
        return redirect('crm_task_list')
    users = User.objects.all()
    contacts = Contact.objects.all()
    deals = Deal.objects.all()
    return render(request, 'crm/task_form.html', {
        'task': task, 'contacts': contacts, 'deals': deals, 'users': users, 'title': 'Modifier la tâche',
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(CrmTask, pk=pk)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Tâche "{title}" supprimée.')
        return redirect('crm_task_list')
    return render(request, 'crm/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle(request, pk):
    task = get_object_or_404(CrmTask, pk=pk)
    task.completed = not task.completed
    task.save()
    messages.success(request, f'Tâche "{task.title}" {"terminée" if task.completed else "rouverte"}.')
    return redirect('crm_task_list')


@login_required
def export_companies_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="societes.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Secteur', 'Adresse', 'Code postal', 'Ville', 'Pays', 'Téléphone', 'Email', 'Site web', 'SIRET'])
    for c in Company.objects.all():
        writer.writerow([c.name, c.sector, c.address, c.postal_code, c.city, c.country, c.phone, c.email, c.website, c.siret])
    return response


@login_required
def export_contacts_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Prénom', 'Nom', 'Email', 'Téléphone', 'Portable', 'Fonction', 'Société'])
    for c in Contact.objects.select_related('company').all():
        writer.writerow([c.first_name, c.last_name, c.email, c.phone, c.mobile, c.function, c.company.name if c.company else ''])
    return response


@login_required
def export_deals_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="affaires.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Titre', 'Société', 'Contact', 'Montant', 'Probabilité', 'Étape', 'Clôture prévue'])
    for d in Deal.objects.select_related('company', 'contact').all():
        writer.writerow([d.title, d.company.name if d.company else '', str(d.contact) if d.contact else '', d.amount, d.probability, d.get_stage_display(), d.expected_close_date])
    return response


@login_required
def deal_create_quotation(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    from apps.erp.models import Quotation
    quotation = Quotation.objects.create(
        company=deal.company,
        contact=deal.contact,
        deal=deal,
        notes=f'Devis créé depuis l\'affaire CRM : {deal.title}',
        created_by=request.user,
        status='brouillon',
    )
    messages.success(request, f'Devis {quotation.number} créé depuis l\'affaire.')
    return redirect('erp_quotation_detail', pk=quotation.pk)


@login_required
def deal_upload_attachment(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        CrmAttachment.objects.create(deal=deal, file=f, uploaded_by=request.user)
        messages.success(request, f'Fichier "{f.name}" ajouté à l\'affaire.')
    return redirect('crm_deal_detail', pk=deal.pk)


@login_required
def interaction_upload_attachment(request, pk):
    interaction = get_object_or_404(Interaction, pk=pk)
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        CrmAttachment.objects.create(interaction=interaction, file=f, uploaded_by=request.user)
        messages.success(request, f'Fichier "{f.name}" ajouté à l\'interaction.')
    return redirect('crm_interaction_list')


@login_required
def serve_attachment(request, pk):
    from django.http import FileResponse
    att = get_object_or_404(CrmAttachment, pk=pk)
    response = FileResponse(att.file.open('rb'), content_type='application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{att.filename}"'
    return response


@login_required
def delete_attachment(request, pk):
    att = get_object_or_404(CrmAttachment, pk=pk)
    if request.method == 'POST':
        att.file.delete(False)
        att.delete()
        messages.success(request, f'Fichier "{att.filename}" supprimé.')
    if att.deal_id:
        return redirect('crm_deal_detail', pk=att.deal_id)
    return redirect('crm_interaction_list')


@login_required
def import_csv(request):
    import io
    results = {'companies': 0, 'contacts': 0, 'errors': []}
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        if not file.name.endswith('.csv'):
            messages.error(request, 'Le fichier doit être au format CSV.')
            return render(request, 'crm/import_csv.html', {'results': results})
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        headers = reader.fieldnames or []
        has_company_headers = 'Nom' in headers and 'Secteur' in headers
        has_contact_headers = 'Prénom' in headers and 'Nom' in headers
        if not has_company_headers and not has_contact_headers:
            messages.error(request, 'Format non reconnu. Utilisez le modèle CSV (sociétés ou contacts).')
            return render(request, 'crm/import_csv.html', {'results': results})
        for row_num, row in enumerate(reader, 1):
            try:
                if has_company_headers and row.get('Nom', '').strip():
                    Company.objects.create(
                        name=row.get('Nom', '').strip(),
                        sector=row.get('Secteur', '').strip(),
                        address=row.get('Adresse', '').strip(),
                        postal_code=row.get('Code postal', '').strip(),
                        city=row.get('Ville', '').strip(),
                        country=row.get('Pays', 'France').strip(),
                        phone=row.get('Téléphone', '').strip(),
                        email=row.get('Email', '').strip(),
                        website=row.get('Site web', '').strip(),
                        siret=row.get('SIRET', '').strip(),
                        created_by=request.user,
                    )
                    results['companies'] += 1
                elif has_contact_headers and row.get('Prénom', '').strip():
                    company_name = row.get('Société', '').strip()
                    company = Company.objects.filter(name__iexact=company_name).first() if company_name else None
                    Contact.objects.create(
                        company=company,
                        first_name=row.get('Prénom', '').strip(),
                        last_name=row.get('Nom', '').strip(),
                        email=row.get('Email', '').strip(),
                        phone=row.get('Téléphone', '').strip(),
                        mobile=row.get('Portable', '').strip(),
                        function=row.get('Fonction', '').strip(),
                        created_by=request.user,
                    )
                    results['contacts'] += 1
            except Exception as e:
                results['errors'].append(f'Ligne {row_num}: {e}')
        total = results['companies'] + results['contacts']
        if total:
            messages.success(request, f'{total} enregistrement(s) importé(s) avec succès.')
        if results['errors']:
            messages.warning(request, f'{len(results["errors"])} erreur(s) lors de l\'import.')
    return render(request, 'crm/import_csv.html', {'results': results})
