from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import TestScenario, TestStep, TestCampaign, CampaignTest, TestAttachment
from apps.alm.projects.models import Project
from apps.alm.projects.views import can_access_project
from apps.alm.requirements.models import Requirement


@login_required
def test_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    tests = project.test_scenarios.all()
    return render(request, 'alm/tests/test_list.html', {'project': project, 'tests': tests})


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
def campaign_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_access_project(project, request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project_list')
    campaigns = project.campaigns.all()
    return render(request, 'alm/tests/campaign_list.html', {'project': project, 'campaigns': campaigns})


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
