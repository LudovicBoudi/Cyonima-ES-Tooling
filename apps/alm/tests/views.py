from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import TestScenario, TestStep, TestCampaign, CampaignTest, TestAttachment, TestExecution
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project
from apps.alm.requirements.models import Requirement


@login_required
def test_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    q_val = request.GET.get('q', '')
    r_val = request.GET.get('req', '')
    tests = project.test_scenarios.select_related('project').prefetch_related('requirements').all()
    if q_val:
        tests = tests.filter(Q(name__icontains=q_val) | Q(description__icontains=q_val) | Q(number__icontains=q_val))
    if r_val:
        tests = tests.filter(requirements__id=r_val)
    paginator = Paginator(tests, 25)
    page = paginator.get_page(request.GET.get('page'))
    all_reqs = project.requirements.exclude(category='folder')
    return render(request, 'alm/tests/test_list.html', {
        'project': project, 'tests': page, 'q': q_val, 'filter_req': r_val, 'all_reqs': all_reqs,
    })


@login_required
def test_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    requirements = project.requirements.exclude(category='folder')
    if request.method == 'POST':
        scenario = TestScenario.objects.create(
            project=project,
            name=request.POST['name'],
            execution_conditions=request.POST.get('execution_conditions', ''),
            description=request.POST.get('description', ''),
        )
        req_ids = request.POST.getlist('requirements')
        if req_ids:
            scenario.requirements.set(Requirement.objects.filter(id__in=req_ids))
        for i in range(1, 11):
            action = request.POST.get(f'action_{i}')
            expected = request.POST.get(f'expected_{i}')
            if action and expected:
                TestStep.objects.create(
                    test_scenario=scenario,
                    step_number=i,
                    action=action,
                    expected_result=expected,
                )
        messages.success(request, "Scénario de test créé.")
        return redirect('test_list', project_id=project.id)
    return render(request, 'alm/tests/test_form.html', {
        'project': project, 'requirements': requirements, 'title': 'Nouveau test'
    })


@login_required
def test_edit(request, project_id, test_id):
    project = get_object_or_404(Project, id=project_id)
    scenario = get_object_or_404(TestScenario, id=test_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    requirements = project.requirements.exclude(category='folder')
    if request.method == 'POST':
        scenario.name = request.POST['name']
        scenario.execution_conditions = request.POST.get('execution_conditions', '')
        scenario.description = request.POST.get('description', '')
        scenario.save()
        req_ids = request.POST.getlist('requirements')
        scenario.requirements.set(Requirement.objects.filter(id__in=req_ids))
        scenario.steps.all().delete()
        for i in range(1, 11):
            action = request.POST.get(f'action_{i}')
            expected = request.POST.get(f'expected_{i}')
            if action and expected:
                TestStep.objects.create(
                    test_scenario=scenario,
                    step_number=i,
                    action=action,
                    expected_result=expected,
                )
        messages.success(request, "Scénario modifié.")
        return redirect('test_list', project_id=project.id)
    return render(request, 'alm/tests/test_form.html', {
        'project': project, 'scenario': scenario, 'requirements': requirements, 'title': 'Modifier test'
    })


@login_required
def test_delete(request, project_id, test_id):
    project = get_object_or_404(Project, id=project_id)
    scenario = get_object_or_404(TestScenario, id=test_id, project=project)
    if request.method == 'POST':
        scenario.delete()
        messages.success(request, "Scénario supprimé.")
        return redirect('test_list', project_id=project.id)
    return render(request, 'alm/tests/test_confirm_delete.html', {'project': project, 'scenario': scenario})


@login_required
def test_execute(request, project_id, test_id):
    project = get_object_or_404(Project, id=project_id)
    scenario = get_object_or_404(TestScenario, id=test_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    last_exec = scenario.executions.order_by('-executed_at').first()
    if request.method == 'POST':
        result = request.POST.get('result', 'en_echec')
        notes = request.POST.get('notes', '')
        step_results = {}
        for step in scenario.steps.all():
            sr = request.POST.get(f'step_{step.id}', 'reussi')
            step_results[f'step_{step.id}'] = sr
        TestExecution.objects.create(
            test_scenario=scenario,
            executed_by=request.user,
            result=result,
            notes=notes,
            step_results=step_results,
        )
        messages.success(request, "Exécution enregistrée.")
        return redirect('test_list', project_id=project.id)
    return render(request, 'alm/tests/test_execute.html', {
        'project': project, 'scenario': scenario, 'last_exec': last_exec,
    })


@login_required
def test_export_csv(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    import csv
    from django.http import HttpResponse
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="tests_{project.id}.csv"'
    resp.write('\ufeff')
    w = csv.writer(resp)
    w.writerow(['N°', 'Nom', 'Description', 'Conditions', 'Étapes'])
    for t in project.test_scenarios.all().order_by('number'):
        steps = '; '.join([f"{s.step_number}: {s.action} -> {s.expected_result}" for s in t.steps.all()])
        w.writerow([t.get_formatted_number(), t.name, t.description, t.execution_conditions, steps])
    return resp


@login_required
def campaign_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    q_val = request.GET.get('q', '')
    campaigns = project.campaigns.all()
    if q_val:
        campaigns = campaigns.filter(Q(name__icontains=q_val) | Q(description__icontains=q_val))
    paginator = Paginator(campaigns, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'alm/tests/campaign_list.html', {
        'project': project, 'campaigns': page, 'q': q_val,
    })


@login_required
def campaign_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    if request.method == 'POST':
        TestCampaign.objects.create(
            project=project,
            name=request.POST['name'],
            description=request.POST.get('description', ''),
        )
        messages.success(request, "Campagne créée.")
        return redirect('campaign_list', project_id=project.id)
    return render(request, 'alm/tests/campaign_form.html', {'project': project, 'title': 'Nouvelle campagne'})


@login_required
def campaign_detail(request, project_id, campaign_id):
    project = get_object_or_404(Project, id=project_id)
    campaign = get_object_or_404(TestCampaign, id=campaign_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    columns = {
        'backlog': campaign.tests.filter(status='backlog'),
        'en_cours': campaign.tests.filter(status='en_cours'),
        'verifie': campaign.tests.filter(status='verifie'),
        'valide': campaign.tests.filter(status='valide'),
    }
    return render(request, 'alm/tests/campaign_detail.html', {'project': project, 'campaign': campaign, 'columns': columns})


@login_required
def campaign_add_tests(request, project_id, campaign_id):
    project = get_object_or_404(Project, id=project_id)
    campaign = get_object_or_404(TestCampaign, id=campaign_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    available = project.test_scenarios.exclude(
        id__in=campaign.tests.values('test_scenario_id')
    )
    if request.method == 'POST':
        test_ids = request.POST.getlist('tests')
        for idx, tid in enumerate(test_ids):
            CampaignTest.objects.create(
                campaign=campaign,
                test_scenario_id=tid,
                position=idx,
            )
        messages.success(request, "Tests ajoutés à la campagne.")
        return redirect('campaign_detail', project_id=project.id, campaign_id=campaign.id)
    return render(request, 'alm/tests/campaign_add_tests.html', {
        'project': project, 'campaign': campaign, 'available': available
    })


@login_required
def campaign_update_status(request, project_id, campaign_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        for item in data:
            CampaignTest.objects.filter(id=item['id']).update(
                status=item['status'],
                position=item.get('position', 0),
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def campaign_delete(request, project_id, campaign_id):
    project = get_object_or_404(Project, id=project_id)
    campaign = get_object_or_404(TestCampaign, id=campaign_id, project=project)
    if request.method == 'POST':
        campaign.delete()
        messages.success(request, "Campagne supprimée.")
        return redirect('campaign_list', project_id=project.id)
    return render(request, 'alm/tests/campaign_confirm_delete.html', {'project': project, 'campaign': campaign})


@login_required
def campaign_report(request, project_id, campaign_id):
    project = get_object_or_404(Project, id=project_id)
    campaign = get_object_or_404(TestCampaign, id=campaign_id, project=project)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tests_qs = campaign.tests.select_related('test_scenario').all()
    total = tests_qs.count()
    counts = [(code, tests_qs.filter(status=code).count()) for code, _ in CampaignTest.STATUS_CHOICES]
    return render(request, 'alm/tests/campaign_report.html', {
        'project': project, 'campaign': campaign, 'tests': tests_qs,
        'total': total, 'counts': counts, 'status_choices': CampaignTest.STATUS_CHOICES,
    })


@login_required
def campaign_export_csv(request, project_id, campaign_id):
    project = get_object_or_404(Project, id=project_id)
    campaign = get_object_or_404(TestCampaign, id=campaign_id, project=project)
    import csv
    from django.http import HttpResponse
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="campagne_{campaign.id}.csv"'
    resp.write('\ufeff')
    w = csv.writer(resp)
    w.writerow(['Test', 'Statut', 'Position'])
    for ct in campaign.tests.select_related('test_scenario').all().order_by('position'):
        w.writerow([ct.test_scenario.get_formatted_number() + ' - ' + ct.test_scenario.name, ct.get_status_display(), ct.position])
    return resp
