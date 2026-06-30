from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date as date_cls
import calendar as cal_mod
from .models import Employee, Department, Contract, LeaveRequest


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
    return render(request, 'hr/employee_detail.html', {
        'employee': employee, 'contracts': contracts, 'leaves': leaves,
    })


@staff_member_required
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
    })


@staff_member_required
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
    })


@staff_member_required
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


@staff_member_required
def department_create(request):
    if request.method == 'POST':
        dept = Department.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
        )
        messages.success(request, f'Département "{dept.name}" créé.')
        return redirect('hr_department_list')
    return render(request, 'hr/department_form.html', {'title': 'Nouveau département'})


@staff_member_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.name = request.POST['name']
        dept.description = request.POST.get('description', '')
        dept.save()
        messages.success(request, f'Département "{dept.name}" modifié.')
        return redirect('hr_department_list')
    return render(request, 'hr/department_form.html', {
        'department': dept, 'title': 'Modifier le département',
    })


@staff_member_required
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
    return render(request, 'hr/contract_list.html', {'contracts': contracts})


@staff_member_required
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


@staff_member_required
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


@staff_member_required
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


@staff_member_required
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


@staff_member_required
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


@staff_member_required
def leave_delete(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Demande de congé supprimée.')
        return redirect('hr_leave_list')
    return render(request, 'hr/leave_confirm_delete.html', {'leave': leave})


@staff_member_required
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'valide'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, f'Congé {leave} validé.')
    return redirect('hr_leave_list')


@staff_member_required
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'refuse'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, f'Congé {leave} refusé.')
    return redirect('hr_leave_list')
