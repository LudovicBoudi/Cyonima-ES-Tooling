from django.contrib import admin
from .models import Employee, Department, Contract, LeaveRequest, Diploma, Certification, Training, Employment, Cv, Evaluation

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'department', 'job_title', 'grade', 'status', 'user']
    list_filter = ['department', 'status', 'grade']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['employee', 'get_type_display', 'start_date', 'end_date', 'salary']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'get_type_display', 'start_date', 'end_date', 'status']

@admin.register(Diploma)
class DiplomaAdmin(admin.ModelAdmin):
    list_display = ['employee', 'name', 'get_level_display', 'year']

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'name', 'company', 'year']

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['employee', 'name', 'organization', 'year']

@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'job_title', 'employer', 'start_date', 'end_date']

@admin.register(Cv)
class CvAdmin(admin.ModelAdmin):
    list_display = ['employee', 'uploaded_at']

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'year', 'rating', 'evaluator', 'created_at']
