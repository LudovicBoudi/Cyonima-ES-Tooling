from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Company, Contact, Deal, Interaction, CrmTask


def _can_access(user):
    return True


@login_required
def dashboard(request):
    total_companies = Company.objects.count()
    total_contacts = Contact.objects.count()
    total_deals = Deal.objects.count()
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

    won_amount = Deal.objects.filter(stage='gagne').aggregate(Sum('amount'))['amount__sum'] or 0
    lost_amount = Deal.objects.filter(stage='perdu').aggregate(Sum('amount'))['amount__sum'] or 0

    recent_interactions = Interaction.objects.select_related('contact', 'created_by')[:10]

    upcoming_tasks = CrmTask.objects.filter(completed=False).order_by('due_date', '-created_at')[:10]

    overdue_tasks_count = CrmTask.objects.filter(completed=False, due_date__lt=timezone.now().date()).count()

    return render(request, 'crm/dashboard.html', {
        'total_companies': total_companies,
        'total_contacts': total_contacts,
        'total_deals': total_deals,
        'active_deals': active_deals,
        'pipeline_value': pipeline_value,
        'deals_by_stage': deals_by_stage_sorted,
        'won_amount': won_amount,
        'lost_amount': lost_amount,
        'recent_interactions': recent_interactions,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks_count': overdue_tasks_count,
    })


@login_required
def company_list(request):
    companies = Company.objects.annotate(contact_count=Count('contacts'), deal_count=Count('deals'))
    return render(request, 'crm/company_list.html', {'companies': companies})


@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    contacts = company.contacts.all()
    deals = company.deals.all()
    return render(request, 'crm/company_detail.html', {
        'company': company, 'contacts': contacts, 'deals': deals,
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
    return render(request, 'crm/contact_list.html', {'contacts': contacts})


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
    return render(request, 'crm/deal_list.html', {'deals': deals})


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
        deal.title = request.POST['title']
        deal.company_id = request.POST.get('company') or None
        deal.contact_id = contact_pk if contact_pk else None
        deal.amount = request.POST.get('amount', 0)
        deal.probability = request.POST.get('probability', 0)
        deal.stage = request.POST.get('stage', 'prospection')
        deal.expected_close_date = request.POST.get('expected_close_date') or None
        deal.description = request.POST.get('description', '')
        deal.save()
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
def interaction_list(request):
    contact_pk = request.GET.get('contact')
    deal_pk = request.GET.get('deal')
    interactions = Interaction.objects.select_related('contact', 'deal', 'created_by').all()
    if contact_pk:
        interactions = interactions.filter(contact_id=contact_pk)
    if deal_pk:
        interactions = interactions.filter(deal_id=deal_pk)
    return render(request, 'crm/interaction_list.html', {
        'interactions': interactions,
        'contacts': Contact.objects.all(),
        'deals': Deal.objects.all(),
        'filter_contact': contact_pk,
        'filter_deal': deal_pk,
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
    return render(request, 'crm/task_list.html', {'tasks': tasks})


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
