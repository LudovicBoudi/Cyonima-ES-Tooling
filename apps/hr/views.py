from functools import wraps
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date as date_cls
import calendar as cal_mod
from .models import Employee, Department, Contract, LeaveRequest, Diploma, Certification, Training, Employment, Cv, Evaluation, DIPLOMA_LEVELS


def hrbp_or_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès refusé.")
        profile = getattr(request.user, 'profile', None)
        if profile and (profile.is_admin() or profile.has_role('hrbp')):
            return view_func(request, *args, **kwargs)
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès refusé.")
    return _wrapper


def user_can_view_salary(user):
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile'):
        return False
    return user.profile.is_admin() or user.profile.has_role('hrbp')


@staff_member_required
def dashboard(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='actif').count()
    trial_employees = Employee.objects.filter(status='essai').count()
    on_leave = Employee.objects.filter(status='conges').count()

    today = timezone.now().date()
    pending_leaves = LeaveRequest.objects.filter(status='demande').count()
    active_contracts = Contract.objects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).count()

    employees_by_dept = []
    for dept in Department.objects.annotate(count=Count('employees')):
        employees_by_dept.append({'name': dept.name, 'count': dept.count})

    contracts_by_type = []
    for code, label in Contract.TYPE_CHOICES:
        cnt = Contract.objects.filter(type=code).count()
        if cnt:
            contracts_by_type.append({'label': label, 'count': cnt})

    leaves_this_month = LeaveRequest.objects.filter(
        start_date__month=today.month, start_date__year=today.year
    ).count()

    recent_leaves = LeaveRequest.objects.select_related('employee').order_by('-created_at')[:10]

    upcoming_birthdays = Employee.objects.filter(
        birth_date__month=today.month,
        birth_date__day__gte=today.day,
        status__in=['actif', 'essai', 'conges'],
    ).order_by('birth_date__day')[:5]

    return render(request, 'hr/dashboard.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'trial_employees': trial_employees,
        'on_leave': on_leave,
        'pending_leaves': pending_leaves,
        'active_contracts': active_contracts,
        'employees_by_dept': employees_by_dept,
        'contracts_by_type': contracts_by_type,
        'leaves_this_month': leaves_this_month,
        'recent_leaves': recent_leaves,
        'upcoming_birthdays': upcoming_birthdays,
    })


@staff_member_required
def employee_list(request):
    employees = Employee.objects.select_related('department').all()
    return render(request, 'hr/employee_list.html', {'employees': employees})


@staff_member_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    contracts = employee.contracts.all()
    leaves = employee.leave_requests.all()
    diplomas = employee.diplomas.all()
    certifications = employee.certifications.all()
    trainings = employee.trainings.all()
    employments = employee.employments.all()
    cvs = employee.cvs.all()
    evaluations = employee.evaluations.all()
    return render(request, 'hr/employee_detail.html', {
        'employee': employee, 'contracts': contracts, 'leaves': leaves,
        'diplomas': diplomas, 'certifications': certifications, 'trainings': trainings,
        'employments': employments, 'cvs': cvs, 'evaluations': evaluations,
        'can_view_salary': user_can_view_salary(request.user),
    })


@hrbp_or_admin_required
def employee_create(request):
    if request.method == 'POST':
        emp = Employee.objects.create(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            mobile=request.POST.get('mobile', ''),
            department_id=request.POST.get('department') or None,
            job_title=request.POST.get('job_title', ''),
            grade=request.POST.get('grade', ''),
            hire_date=request.POST.get('hire_date') or None,
            status=request.POST.get('status', 'actif'),
            birth_date=request.POST.get('birth_date') or None,
            address=request.POST.get('address', ''),
            emergency_contact=request.POST.get('emergency_contact', ''),
            emergency_phone=request.POST.get('emergency_phone', ''),
            company=request.POST.get('company', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Employé {emp} créé.')
        return redirect('hr_employee_detail', pk=emp.pk)
    departments = Department.objects.all()
    return render(request, 'hr/employee_form.html', {
        'departments': departments, 'title': 'Nouvel employé',
        'status_choices': Employee.STATUS_CHOICES,
        'grade_choices': Employee._meta.get_field('grade').choices,
    })


@hrbp_or_admin_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.first_name = request.POST['first_name']
        employee.last_name = request.POST['last_name']
        employee.email = request.POST.get('email', '')
        employee.phone = request.POST.get('phone', '')
        employee.mobile = request.POST.get('mobile', '')
        employee.department_id = request.POST.get('department') or None
        employee.job_title = request.POST.get('job_title', '')
        employee.grade = request.POST.get('grade', '')
        employee.hire_date = request.POST.get('hire_date') or None
        employee.status = request.POST.get('status', 'actif')
        employee.birth_date = request.POST.get('birth_date') or None
        employee.address = request.POST.get('address', '')
        employee.emergency_contact = request.POST.get('emergency_contact', '')
        employee.emergency_phone = request.POST.get('emergency_phone', '')
        employee.company = request.POST.get('company', '')
        employee.notes = request.POST.get('notes', '')
        employee.save()
        messages.success(request, f'Employé {employee} modifié.')
        return redirect('hr_employee_detail', pk=employee.pk)
    departments = Department.objects.all()
    return render(request, 'hr/employee_form.html', {
        'employee': employee, 'departments': departments, 'title': 'Modifier l\'employé',
        'status_choices': Employee.STATUS_CHOICES,
        'grade_choices': Employee._meta.get_field('grade').choices,
    })


@hrbp_or_admin_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        name = str(employee)
        employee.delete()
        messages.success(request, f'Employé {name} supprimé.')
        return redirect('hr_employee_list')
    return render(request, 'hr/employee_confirm_delete.html', {'employee': employee})


@staff_member_required
def department_list(request):
    departments = Department.objects.annotate(emp_count=Count('employees'))
    return render(request, 'hr/department_list.html', {'departments': departments})


@hrbp_or_admin_required
def department_create(request):
    if request.method == 'POST':
        dept = Department.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            manager_id=request.POST.get('manager') or None,
        )
        messages.success(request, f'Département "{dept.name}" créé.')
        return redirect('hr_department_list')
    employees = Employee.objects.all()
    return render(request, 'hr/department_form.html', {'title': 'Nouveau département', 'employees': employees})


@hrbp_or_admin_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.name = request.POST['name']
        dept.description = request.POST.get('description', '')
        dept.manager_id = request.POST.get('manager') or None
        dept.save()
        messages.success(request, f'Département "{dept.name}" modifié.')
        return redirect('hr_department_list')
    employees = Employee.objects.all()
    return render(request, 'hr/department_form.html', {
        'department': dept, 'title': 'Modifier le département', 'employees': employees,
    })


@hrbp_or_admin_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = dept.name
        dept.delete()
        messages.success(request, f'Département "{name}" supprimé.')
        return redirect('hr_department_list')
    return render(request, 'hr/department_confirm_delete.html', {'department': dept})


@staff_member_required
def contract_list(request):
    contracts = Contract.objects.select_related('employee', 'employee__department')
    today = timezone.now().date()
    for c in contracts:
        if not c.end_date or c.type == 'cdi':
            c.row_color = 'green'
        else:
            remaining = (c.end_date - today).days
            if remaining < 0:
                c.row_color = 'red'
            elif remaining <= 7:
                c.row_color = 'red'
            elif remaining <= 30:
                c.row_color = 'orange'
            elif remaining <= 90:
                c.row_color = 'yellow'
            else:
                c.row_color = 'green'
    return render(request, 'hr/contract_list.html', {'contracts': contracts, 'can_view_salary': user_can_view_salary(request.user)})


@hrbp_or_admin_required
def contract_create(request):
    if request.method == 'POST':
        c = Contract.objects.create(
            employee_id=request.POST['employee'],
            type=request.POST['type'],
            start_date=request.POST['start_date'],
            end_date=request.POST.get('end_date') or None,
            salary=request.POST.get('salary', 0),
            position=request.POST.get('position', ''),
            description=request.POST.get('description', ''),
            created_by=request.user,
        )
        messages.success(request, 'Contrat créé.')
        return redirect('hr_contract_list')
    employees = Employee.objects.all()
    return render(request, 'hr/contract_form.html', {
        'employees': employees, 'title': 'Nouveau contrat',
        'type_choices': Contract.TYPE_CHOICES,
    })


@hrbp_or_admin_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        contract.employee_id = request.POST['employee']
        contract.type = request.POST['type']
        contract.start_date = request.POST['start_date']
        contract.end_date = request.POST.get('end_date') or None
        contract.salary = request.POST.get('salary', 0)
        contract.position = request.POST.get('position', '')
        contract.description = request.POST.get('description', '')
        contract.save()
        messages.success(request, 'Contrat modifié.')
        return redirect('hr_contract_list')
    employees = Employee.objects.all()
    return render(request, 'hr/contract_form.html', {
        'contract': contract, 'employees': employees, 'title': 'Modifier le contrat',
        'type_choices': Contract.TYPE_CHOICES,
    })


@hrbp_or_admin_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contrat supprimé.')
        return redirect('hr_contract_list')
    return render(request, 'hr/contract_confirm_delete.html', {'contract': contract})


@staff_member_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related('employee', 'employee__department', 'approved_by').all()

    all_leaves = list(leaves)
    leave_by_id = {l.pk: l for l in all_leaves}

    dept_groups = {}
    for l in all_leaves:
        dept_id = l.employee.department_id
        dept_groups.setdefault(dept_id, []).append(l)

    conflict_ids = set()
    for dept_id, group in dept_groups.items():
        active = [l for l in group if l.status in ('demande', 'valide')]
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                a, b = active[i], active[j]
                if a.start_date <= b.end_date and b.start_date <= a.end_date:
                    conflict_ids.add(a.pk)
                    conflict_ids.add(b.pk)

    for l in all_leaves:
        if l.status == 'refuse':
            l.row_color = 'yellow'
        elif l.status == 'valide' and l.pk in conflict_ids:
            l.row_color = 'orange'
        elif l.status == 'valide':
            l.row_color = 'green'
        elif l.status == 'demande' and l.pk in conflict_ids:
            l.row_color = 'orange'
        else:
            l.row_color = None

    today = timezone.now().date()
    year = request.GET.get('year')
    month = request.GET.get('month')
    if year and month:
        year, month = int(year), int(month)
    else:
        year, month = today.year, today.month

    _, days_in_month = cal_mod.monthrange(year, month)
    first_weekday = date_cls(year, month, 1).weekday()

    month_names = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                   'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    type_colors = {
        'cp': 'bg-blue-500', 'rtt': 'bg-teal-500', 'maladie': 'bg-red-500',
        'maternite': 'bg-pink-500', 'sans_solde': 'bg-gray-500', 'formation': 'bg-purple-500',
    }

    active_leaves = [l for l in all_leaves if l.status in ('demande', 'valide')]
    weeks = []
    week = [None] * first_weekday
    for day in range(1, days_in_month + 1):
        d = date_cls(year, month, day)
        day_leaves = []
        for l in active_leaves:
            if l.start_date <= d <= l.end_date:
                initials = ''.join(p[0].upper() for p in l.employee.first_name.split() + l.employee.last_name.split()[:1])
                if len(initials) > 2:
                    initials = initials[:2]
                day_leaves.append({
                    'employee': str(l.employee),
                    'initials': initials,
                    'type': l.type,
                    'color': type_colors.get(l.type, 'bg-blue-500'),
                    'status': l.status,
                })
        week.append({'day': day, 'is_today': d == today, 'leaves': day_leaves})
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        week += [None] * (7 - len(week))
        weeks.append(week)

    prev_m = month - 1 or 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1

    calendar_data = {
        'year': year,
        'month': month,
        'month_name': month_names[month - 1],
        'prev_year': prev_y,
        'prev_month': prev_m,
        'next_year': next_y,
        'next_month': next_m,
        'weeks': weeks,
    }

    return render(request, 'hr/leave_list.html', {'leaves': all_leaves, 'calendar': calendar_data})


@hrbp_or_admin_required
def leave_create(request):
    if request.method == 'POST':
        l = LeaveRequest.objects.create(
            employee_id=request.POST['employee'],
            type=request.POST['type'],
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date'],
            reason=request.POST.get('reason', ''),
            created_by=request.user,
        )
        messages.success(request, 'Demande de congé créée.')
        return redirect('hr_leave_list')
    employees = Employee.objects.all()
    return render(request, 'hr/leave_form.html', {
        'employees': employees, 'title': 'Nouvelle demande',
        'type_choices': LeaveRequest.TYPE_CHOICES,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    })


@hrbp_or_admin_required
def leave_edit(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        leave.employee_id = request.POST['employee']
        leave.type = request.POST['type']
        leave.start_date = request.POST['start_date']
        leave.end_date = request.POST['end_date']
        leave.reason = request.POST.get('reason', '')
        leave.save()
        messages.success(request, 'Demande de congé modifiée.')
        return redirect('hr_leave_list')
    employees = Employee.objects.all()
    return render(request, 'hr/leave_form.html', {
        'leave': leave, 'employees': employees, 'title': 'Modifier la demande',
        'type_choices': LeaveRequest.TYPE_CHOICES,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    })


@hrbp_or_admin_required
def leave_delete(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Demande de congé supprimée.')
        return redirect('hr_leave_list')
    return render(request, 'hr/leave_confirm_delete.html', {'leave': leave})


@hrbp_or_admin_required
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_leave_list')
    leave.status = 'valide'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, f'Congé {leave} validé.')
    return redirect('hr_leave_list')


@hrbp_or_admin_required
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_leave_list')
    leave.status = 'refuse'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, f'Congé {leave} refusé.')
    return redirect('hr_leave_list')


@login_required
def profil(request):
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, "Aucune fiche employ\u00e9 n'est associ\u00e9e \u00e0 votre compte.")
        return redirect('home')
    diplomas = employee.diplomas.all()
    certifications = employee.certifications.all()
    trainings = employee.trainings.all()
    employments = employee.employments.all()
    cvs = employee.cvs.all()
    evaluations = employee.evaluations.all()
    return render(request, 'hr/profil.html', {
        'employee': employee,
        'diplomas': diplomas,
        'certifications': certifications,
        'trainings': trainings,
        'employments': employments,
        'cvs': cvs,
        'evaluations': evaluations,
    })


@login_required
def diplome_create(request):
    employee = get_object_or_404(Employee, user=request.user)
    if request.method == 'POST':
        d = Diploma.objects.create(
            employee=employee,
            level=request.POST['level'],
            name=request.POST['name'],
            school=request.POST['school'],
            year=request.POST['year'],
            file=request.FILES.get('file'),
        )
        messages.success(request, f'Dipl\u00f4me "{d.name}" ajout\u00e9.')
        return redirect('hr_profil')
    return render(request, 'hr/diplome_form.html', {
        'diploma_levels': DIPLOMA_LEVELS,
        'title': 'Ajouter un dipl\u00f4me',
    })


@login_required
def diplome_edit(request, pk):
    diploma = get_object_or_404(Diploma, pk=pk, employee__user=request.user)
    if request.method == 'POST':
        diploma.level = request.POST['level']
        diploma.name = request.POST['name']
        diploma.school = request.POST['school']
        diploma.year = request.POST['year']
        if request.FILES.get('file'):
            diploma.file = request.FILES['file']
        diploma.save()
        messages.success(request, f'Dipl\u00f4me "{diploma.name}" modifi\u00e9.')
        return redirect('hr_profil')
    return render(request, 'hr/diplome_form.html', {
        'diploma': diploma,
        'diploma_levels': DIPLOMA_LEVELS,
        'title': 'Modifier le dipl\u00f4me',
    })


@login_required
def diplome_delete(request, pk):
    diploma = get_object_or_404(Diploma, pk=pk, employee__user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_profil')
    name = str(diploma)
    diploma.delete()
    messages.success(request, f'Diplôme "{name}" supprimé.')
    return redirect('hr_profil')


@login_required
def certification_create(request):
    employee = get_object_or_404(Employee, user=request.user)
    if request.method == 'POST':
        c = Certification.objects.create(
            employee=employee,
            name=request.POST['name'],
            company=request.POST['company'],
            year=request.POST['year'],
            file=request.FILES.get('file'),
        )
        messages.success(request, f'Certification "{c.name}" ajout\u00e9e.')
        return redirect('hr_profil')
    return render(request, 'hr/certification_form.html', {
        'title': 'Ajouter une certification',
    })


@login_required
def certification_edit(request, pk):
    cert = get_object_or_404(Certification, pk=pk, employee__user=request.user)
    if request.method == 'POST':
        cert.name = request.POST['name']
        cert.company = request.POST['company']
        cert.year = request.POST['year']
        if request.FILES.get('file'):
            cert.file = request.FILES['file']
        cert.save()
        messages.success(request, f'Certification "{cert.name}" modifi\u00e9e.')
        return redirect('hr_profil')
    return render(request, 'hr/certification_form.html', {
        'certification': cert,
        'title': 'Modifier la certification',
    })


@login_required
def certification_delete(request, pk):
    cert = get_object_or_404(Certification, pk=pk, employee__user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_profil')
    name = str(cert)
    cert.delete()
    messages.success(request, f'Certification "{name}" supprimée.')
    return redirect('hr_profil')


@login_required
def training_create(request):
    employee = get_object_or_404(Employee, user=request.user)
    if request.method == 'POST':
        t = Training.objects.create(
            employee=employee,
            name=request.POST['name'],
            organization=request.POST['organization'],
            year=request.POST['year'],
            file=request.FILES.get('file'),
        )
        messages.success(request, f'Formation "{t.name}" ajout\u00e9e.')
        return redirect('hr_profil')
    return render(request, 'hr/training_form.html', {
        'title': 'Ajouter une formation',
    })


@login_required
def training_edit(request, pk):
    training = get_object_or_404(Training, pk=pk, employee__user=request.user)
    if request.method == 'POST':
        training.name = request.POST['name']
        training.organization = request.POST['organization']
        training.year = request.POST['year']
        if request.FILES.get('file'):
            training.file = request.FILES['file']
        training.save()
        messages.success(request, f'Formation "{training.name}" modifi\u00e9e.')
        return redirect('hr_profil')
    return render(request, 'hr/training_form.html', {
        'training': training,
        'title': 'Modifier la formation',
    })


@login_required
def training_delete(request, pk):
    training = get_object_or_404(Training, pk=pk, employee__user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_profil')
    name = str(training)
    training.delete()
    messages.success(request, f'Formation "{name}" supprimée.')
    return redirect('hr_profil')


@login_required
def employment_create(request):
    employee = get_object_or_404(Employee, user=request.user)
    if request.method == 'POST':
        e = Employment.objects.create(
            employee=employee,
            job_title=request.POST['job_title'],
            employer=request.POST['employer'],
            description=request.POST.get('description', ''),
            start_date=request.POST['start_date'],
            end_date=request.POST.get('end_date') or None,
        )
        messages.success(request, f'Emploi "{e.job_title}" ajout\u00e9.')
        return redirect('hr_profil')
    return render(request, 'hr/employment_form.html', {
        'title': 'Ajouter un emploi',
    })


@login_required
def employment_edit(request, pk):
    emp = get_object_or_404(Employment, pk=pk, employee__user=request.user)
    if request.method == 'POST':
        emp.job_title = request.POST['job_title']
        emp.employer = request.POST['employer']
        emp.description = request.POST.get('description', '')
        emp.start_date = request.POST['start_date']
        emp.end_date = request.POST.get('end_date') or None
        emp.save()
        messages.success(request, f'Emploi "{emp.job_title}" modifi\u00e9.')
        return redirect('hr_profil')
    return render(request, 'hr/employment_form.html', {
        'employment': emp,
        'title': 'Modifier l\'emploi',
    })


@login_required
def employment_delete(request, pk):
    emp = get_object_or_404(Employment, pk=pk, employee__user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_profil')
    name = str(emp)
    emp.delete()
    messages.success(request, f'Emploi "{name}" supprimé.')
    return redirect('hr_profil')


@login_required
def cv_upload(request):
    employee = get_object_or_404(Employee, user=request.user)
    if request.method == 'POST':
        f = request.FILES.get('file')
        if f:
            if not f.name.lower().endswith('.pdf'):
                messages.error(request, 'Seuls les fichiers PDF sont accept\u00e9s.')
                return render(request, 'hr/cv_form.html', {'title': 'Ajouter un CV'})
            if f.content_type != 'application/pdf':
                messages.error(request, 'Seuls les fichiers PDF sont accept\u00e9s.')
                return render(request, 'hr/cv_form.html', {'title': 'Ajouter un CV'})
            Cv.objects.create(employee=employee, file=f)
            messages.success(request, 'CV ajout\u00e9.')
            return redirect('hr_profil')
    return render(request, 'hr/cv_form.html', {'title': 'Ajouter un CV'})


@login_required
def cv_delete(request, pk):
    cv = get_object_or_404(Cv, pk=pk, employee__user=request.user)
    if request.method != 'POST':
        messages.error(request, 'Méthode non autorisée.')
        return redirect('hr_profil')
    name = str(cv)
    cv.delete()
    messages.success(request, f'CV "{name}" supprimé.')
    return redirect('hr_profil')


@login_required
@xframe_options_sameorigin
def cv_serve(request, pk):
    cv = get_object_or_404(Cv, pk=pk)
    if not (request.user.is_staff or cv.employee.user == request.user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Acc\u00e8s refus\u00e9.')
    response = FileResponse(cv.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="{}"'.format(cv.file.name.split('/')[-1])
    return response


@hrbp_or_admin_required
def evaluation_create(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    if request.method == 'POST':
        Evaluation.objects.create(
            employee=employee,
            evaluator=request.user,
            year=request.POST.get('year', timezone.now().year),
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment', ''),
        )
        messages.success(request, 'Évaluation enregistrée.')
        return redirect('hr_employee_detail', pk=employee_pk)
    return render(request, 'hr/evaluation_form.html', {
        'employee': employee,
        'title': f'Ajouter une évaluation — {employee}',
    })


@hrbp_or_admin_required
def evaluation_edit(request, pk):
    eval_obj = get_object_or_404(Evaluation, pk=pk)
    if request.method == 'POST':
        eval_obj.year = request.POST.get('year', eval_obj.year)
        eval_obj.rating = request.POST.get('rating', eval_obj.rating)
        eval_obj.comment = request.POST.get('comment', '')
        eval_obj.save()
        messages.success(request, 'Évaluation modifiée.')
        return redirect('hr_employee_detail', pk=eval_obj.employee.pk)
    return render(request, 'hr/evaluation_form.html', {
        'evaluation': eval_obj,
        'employee': eval_obj.employee,
        'title': f'Modifier l\'évaluation {eval_obj.year}',
    })


@hrbp_or_admin_required
def evaluation_delete(request, pk):
    eval_obj = get_object_or_404(Evaluation, pk=pk)
    emp_pk = eval_obj.employee.pk
    eval_obj.delete()
    messages.success(request, 'Évaluation supprimée.')
    return redirect('hr_employee_detail', pk=emp_pk)
