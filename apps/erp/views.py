from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Quotation, Invoice, CreditNote, SupplierInvoice, Payment
from apps.crm.models import Company


@login_required
def dashboard(request):
    now = timezone.now().date()
    month_start = now.replace(day=1)
    first_day_quarter = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1)

    ca_mensuel = Invoice.objects.filter(
        status__in=['emise', 'payee', 'impayee'],
        date__gte=month_start,
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    ca_trimestriel = Invoice.objects.filter(
        status__in=['emise', 'payee', 'impayee'],
        date__gte=first_day_quarter,
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    unpaid = Invoice.objects.filter(status='impayee')
    unpaid_total = unpaid.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    unpaid_count = unpaid.count()

    supplier_unpaid = SupplierInvoice.objects.filter(status='enregistree')
    supplier_unpaid_total = supplier_unpaid.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    supplier_unpaid_count = supplier_unpaid.count()

    recent_quotations = Quotation.objects.all()[:5]
    recent_invoices = Invoice.objects.all()[:5]

    invoices_by_status = []
    for code, label in Invoice.STATUS_CHOICES:
        invoices_by_status.append({
            'code': code, 'label': label,
            'count': Invoice.objects.filter(status=code).count(),
        })

    return render(request, 'erp/dashboard.html', {
        'ca_mensuel': ca_mensuel,
        'ca_trimestriel': ca_trimestriel,
        'unpaid_total': unpaid_total,
        'unpaid_count': unpaid_count,
        'supplier_unpaid_total': supplier_unpaid_total,
        'supplier_unpaid_count': supplier_unpaid_count,
        'recent_quotations': recent_quotations,
        'recent_invoices': recent_invoices,
        'invoices_by_status': invoices_by_status,
    })


# ─── Quotations ───────────────────────────────────────────────────

@login_required
def quotation_list(request):
    quotations = Quotation.objects.select_related('company', 'created_by').all()
    return render(request, 'erp/quotation_list.html', {'quotations': quotations})


@login_required
def quotation_detail(request, pk):
    q = get_object_or_404(Quotation.objects.select_related('company', 'contact', 'created_by'), pk=pk)
    invoices = q.invoices.all()
    return render(request, 'erp/quotation_detail.html', {'q': q, 'invoices': invoices})


@login_required
def quotation_create(request):
    if request.method == 'POST':
        lines_json = request.POST.get('lines_json', '[]')
        import json
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        q = Quotation.objects.create(
            company_id=request.POST.get('company') or None,
            contact_id=request.POST.get('contact') or None,
            valid_until=request.POST.get('valid_until') or None,
            status=request.POST.get('status', 'brouillon'),
            lines=lines,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Devis {q.number} créé.')
        return redirect('erp_quotation_detail', pk=q.pk)
    companies = Company.objects.all()
    return render(request, 'erp/quotation_form.html', {'quotation': None, 'companies': companies, 'status_choices': Quotation.STATUS_CHOICES})


@login_required
def quotation_edit(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        q.company_id = request.POST.get('company') or None
        q.contact_id = request.POST.get('contact') or None
        q.valid_until = request.POST.get('valid_until') or None
        q.status = request.POST.get('status', 'brouillon')
        q.lines = lines
        q.notes = request.POST.get('notes', '')
        q.save()
        messages.success(request, f'Devis {q.number} modifié.')
        return redirect('erp_quotation_detail', pk=q.pk)
    companies = Company.objects.all()
    return render(request, 'erp/quotation_form.html', {'quotation': q, 'companies': companies, 'status_choices': Quotation.STATUS_CHOICES})


@login_required
def quotation_delete(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        q.delete()
        messages.success(request, 'Devis supprimé.')
        return redirect('erp_quotation_list')
    return render(request, 'erp/confirm_delete.html', {'obj': q})


@login_required
def quotation_convert(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    inv = Invoice.objects.create(
        company=q.company,
        contact=q.contact,
        status='brouillon',
        lines=q.lines,
        notes=f'Issu du devis {q.number}',
        quotation=q,
        created_by=request.user,
    )
    q.status = 'accepte'
    q.save()
    messages.success(request, f'Facture {inv.number} créée depuis le devis {q.number}.')
    return redirect('erp_invoice_detail', pk=inv.pk)


# ─── Invoices ──────────────────────────────────────────────────────

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('company', 'created_by').all()
    return render(request, 'erp/invoice_list.html', {'invoices': invoices})


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related('company', 'contact', 'quotation', 'created_by'), pk=pk)
    payments = inv.payments.all()
    credit_notes = inv.credit_notes.all()
    return render(request, 'erp/invoice_detail.html', {'inv': inv, 'payments': payments, 'credit_notes': credit_notes})


@login_required
def invoice_create(request):
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        inv = Invoice.objects.create(
            company_id=request.POST.get('company') or None,
            contact_id=request.POST.get('contact') or None,
            due_date=request.POST.get('due_date') or None,
            status=request.POST.get('status', 'brouillon'),
            lines=lines,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Facture {inv.number} créée.')
        return redirect('erp_invoice_detail', pk=inv.pk)
    companies = Company.objects.all()
    return render(request, 'erp/invoice_form.html', {'invoice': None, 'companies': companies, 'status_choices': Invoice.STATUS_CHOICES})


@login_required
def invoice_edit(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        inv.company_id = request.POST.get('company') or None
        inv.contact_id = request.POST.get('contact') or None
        inv.due_date = request.POST.get('due_date') or None
        inv.status = request.POST.get('status', 'brouillon')
        inv.lines = lines
        inv.notes = request.POST.get('notes', '')
        inv.save()
        messages.success(request, f'Facture {inv.number} modifiée.')
        return redirect('erp_invoice_detail', pk=inv.pk)
    companies = Company.objects.all()
    return render(request, 'erp/invoice_form.html', {'invoice': inv, 'companies': companies, 'status_choices': Invoice.STATUS_CHOICES})


@login_required
def invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        inv.delete()
        messages.success(request, 'Facture supprimée.')
        return redirect('erp_invoice_list')
    return render(request, 'erp/confirm_delete.html', {'obj': inv})


# ─── Credit Notes ─────────────────────────────────────────────────

@login_required
def creditnote_list(request):
    notes = CreditNote.objects.select_related('company', 'invoice', 'created_by').all()
    return render(request, 'erp/creditnote_list.html', {'notes': notes})


@login_required
def creditnote_create(request):
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        cn = CreditNote.objects.create(
            company_id=request.POST.get('company') or None,
            invoice_id=request.POST.get('invoice') or None,
            reason=request.POST.get('reason', ''),
            lines=lines,
            created_by=request.user,
        )
        messages.success(request, f'Avoir {cn.number} créé.')
        return redirect('erp_creditnote_list')
    companies = Company.objects.all()
    invoices = Invoice.objects.all()
    return render(request, 'erp/creditnote_form.html', {'note': None, 'companies': companies, 'invoices': invoices})


@login_required
def creditnote_delete(request, pk):
    cn = get_object_or_404(CreditNote, pk=pk)
    if request.method == 'POST':
        cn.delete()
        messages.success(request, 'Avoir supprimé.')
        return redirect('erp_creditnote_list')
    return render(request, 'erp/confirm_delete.html', {'obj': cn})


# ─── Supplier Invoices ────────────────────────────────────────────

@login_required
def supplier_invoice_list(request):
    invoices = SupplierInvoice.objects.select_related('provider', 'created_by').all()
    return render(request, 'erp/supplier_invoice_list.html', {'invoices': invoices})


@login_required
def supplier_invoice_create(request):
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        inv = SupplierInvoice.objects.create(
            number=request.POST.get('number', ''),
            provider_id=request.POST.get('provider') or None,
            date=request.POST.get('date') or timezone.now().date(),
            due_date=request.POST.get('due_date') or None,
            status=request.POST.get('status', 'brouillon'),
            lines=lines,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Facture fournisseur {inv.internal_number} créée.')
        return redirect('erp_supplier_invoice_list')
    from apps.budget.providers.models import Provider
    providers = Provider.objects.all()
    return render(request, 'erp/supplier_invoice_form.html', {'invoice': None, 'providers': providers, 'status_choices': SupplierInvoice.STATUS_CHOICES})


@login_required
def supplier_invoice_edit(request, pk):
    inv = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        import json
        lines_json = request.POST.get('lines_json', '[]')
        try:
            lines = json.loads(lines_json)
        except json.JSONDecodeError:
            lines = []
        inv.number = request.POST.get('number', '')
        inv.provider_id = request.POST.get('provider') or None
        inv.date = request.POST.get('date') or timezone.now().date()
        inv.due_date = request.POST.get('due_date') or None
        inv.status = request.POST.get('status', 'brouillon')
        inv.lines = lines
        inv.notes = request.POST.get('notes', '')
        inv.save()
        messages.success(request, f'Facture fournisseur {inv.internal_number} modifiée.')
        return redirect('erp_supplier_invoice_list')
    from apps.budget.providers.models import Provider
    providers = Provider.objects.all()
    return render(request, 'erp/supplier_invoice_form.html', {'invoice': inv, 'providers': providers, 'status_choices': SupplierInvoice.STATUS_CHOICES})


@login_required
def supplier_invoice_delete(request, pk):
    inv = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        inv.delete()
        messages.success(request, 'Facture fournisseur supprimée.')
        return redirect('erp_supplier_invoice_list')
    return render(request, 'erp/confirm_delete.html', {'obj': inv})


# ─── Payments ──────────────────────────────────────────────────────

@login_required
def payment_create(request):
    if request.method == 'POST':
        p = Payment.objects.create(
            date=request.POST.get('date') or timezone.now().date(),
            amount=request.POST.get('amount', 0),
            method=request.POST.get('method', 'virement'),
            invoice_id=request.POST.get('invoice') or None,
            supplier_invoice_id=request.POST.get('supplier_invoice') or None,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        # Update paid_amount on linked invoice
        if p.invoice:
            total_paid = p.invoice.payments.aggregate(Sum('amount'))['amount__sum'] or 0
            p.invoice.paid_amount = total_paid
            if total_paid >= p.invoice.total_ttc():
                p.invoice.status = 'payee'
            elif total_paid > 0:
                p.invoice.status = 'impayee'
            p.invoice.save()
        if p.supplier_invoice:
            total_paid = p.supplier_invoice.payments.aggregate(Sum('amount'))['amount__sum'] or 0
            p.supplier_invoice.paid_amount = total_paid
            if total_paid >= p.supplier_invoice.total_ttc():
                p.supplier_invoice.status = 'payee'
            elif total_paid > 0:
                p.supplier_invoice.status = 'enregistree'
            p.supplier_invoice.save()
        messages.success(request, 'Paiement enregistré.')
        return redirect('erp_dashboard')
    invoices = Invoice.objects.filter(status__in=['emise', 'impayee'])
    supplier_invoices = SupplierInvoice.objects.filter(status='enregistree')
    return render(request, 'erp/payment_form.html', {
        'invoices': invoices, 'supplier_invoices': supplier_invoices,
    })
