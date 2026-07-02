from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q, Value as V
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date as dt_date
from django.http import HttpResponse, FileResponse
from weasyprint import HTML
from .models import Quotation, Invoice, CreditNote, SupplierInvoice, Payment, Product, Reminder, ErpAuditLog, vat_breakdown
from .notifications import notify_user, notify_admins, log_audit
from apps.crm.models import Company


@login_required
def dashboard(request):
    now = timezone.now().date()
    month_start = now.replace(day=1)
    first_day_quarter = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1)
    year_start = now.replace(month=1, day=1)

    # KPIs
    ca_mensuel = Invoice.objects.filter(
        status__in=['emise', 'payee', 'impayee'],
        date__gte=month_start,
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    ca_trimestriel = Invoice.objects.filter(
        status__in=['emise', 'payee', 'impayee'],
        date__gte=first_day_quarter,
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    ca_annuel = Invoice.objects.filter(
        status__in=['emise', 'payee', 'impayee'],
        date__gte=year_start,
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    unpaid = Invoice.objects.filter(status='impayee')
    unpaid_count = unpaid.count()
    unpaid_total = sum(inv.total_ttc() for inv in unpaid) or 0

    supplier_unpaid = SupplierInvoice.objects.filter(status='enregistree')
    supplier_unpaid_count = supplier_unpaid.count()
    supplier_unpaid_total = sum(inv.total_ttc() for inv in supplier_unpaid) or 0

    total_quotations = Quotation.objects.count()
    accepted_quotations = Quotation.objects.filter(status='accepte').count()
    conversion_rate = round(accepted_quotations / total_quotations * 100, 1) if total_quotations else 0

    recent_quotations = Quotation.objects.select_related('company').all()[:5]
    recent_invoices = Invoice.objects.select_related('company').all()[:5]

    # Invoices by status (chart)
    invoices_by_status = []
    for code, label in Invoice.STATUS_CHOICES:
        invoices_by_status.append({
            'code': code, 'label': label,
            'count': Invoice.objects.filter(status=code).count(),
        })

    # Monthly evolution (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        start = dt_date(y, m, 1)
        if m == 12:
            end = dt_date(y + 1, 1, 1)
        else:
            end = dt_date(y, m + 1, 1)
        total = Invoice.objects.filter(
            status__in=['emise', 'payee', 'impayee'],
            date__gte=start, date__lt=end,
        ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        count = Invoice.objects.filter(
            date__gte=start, date__lt=end,
        ).count()
        monthly_data.append({'month': start.strftime('%m/%Y'), 'total': float(total), 'count': count})

    # Top 5 clients by CA
    from django.db.models import Value as V
    from django.db.models.functions import Coalesce
    from django.db.models import DecimalField
    top_clients = (
        Invoice.objects.filter(status__in=['emise', 'payee', 'impayee'])
        .values('company__name')
        .annotate(total_ca=Coalesce(Sum('paid_amount'), V(0), output_field=DecimalField()))
        .order_by('-total_ca')[:5]
    )

    return render(request, 'erp/dashboard.html', {
        'ca_mensuel': ca_mensuel,
        'ca_trimestriel': ca_trimestriel,
        'ca_annuel': ca_annuel,
        'unpaid_total': unpaid_total,
        'unpaid_count': unpaid_count,
        'supplier_unpaid_total': supplier_unpaid_total,
        'supplier_unpaid_count': supplier_unpaid_count,
        'total_quotations': total_quotations,
        'accepted_quotations': accepted_quotations,
        'conversion_rate': conversion_rate,
        'recent_quotations': recent_quotations,
        'recent_invoices': recent_invoices,
        'invoices_by_status': invoices_by_status,
        'monthly_data': monthly_data,
        'top_clients': top_clients,
    })


# ─── TVA Report ────────────────────────────────────────────────────

@login_required
def tva_report(request):
    now = timezone.now().date()
    start = request.GET.get('start', now.replace(day=1).isoformat())
    end = request.GET.get('end', now.isoformat())
    from datetime import date as dt_date
    start_dt = dt_date.fromisoformat(start) if isinstance(start, str) else start
    end_dt = dt_date.fromisoformat(end) if isinstance(end, str) else end

    invoices = Invoice.objects.filter(date__gte=start_dt, date__lte=end_dt, status__in=['emise', 'payee', 'impayee'])
    supplier_invs = SupplierInvoice.objects.filter(date__gte=start_dt, date__lte=end_dt, status__in=['enregistree', 'payee'])

    all_rates = {}
    for inv in invoices:
        lines = inv.lines
        for rate, amounts in vat_breakdown(lines).items():
            r = all_rates.setdefault(rate, {'ht_client': 0, 'tva_client': 0, 'ht_fourn': 0, 'tva_fourn': 0})
            r['ht_client'] += amounts['ht']
            r['tva_client'] += amounts['vat']
    for inv in supplier_invs:
        lines = inv.lines
        for rate, amounts in vat_breakdown(lines).items():
            r = all_rates.setdefault(rate, {'ht_client': 0, 'tva_client': 0, 'ht_fourn': 0, 'tva_fourn': 0})
            r['ht_fourn'] += amounts['ht']
            r['tva_fourn'] += amounts['vat']

    total_tva_collectee = sum(r['tva_client'] for r in all_rates.values())
    total_tva_deductible = sum(r['tva_fourn'] for r in all_rates.values())
    tva_net = total_tva_collectee - total_tva_deductible

    sorted_rates = sorted(all_rates.items())

    if request.GET.get('export') == 'csv':
        import csv
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="declaration_tva_{start}_{end}.csv"'
        resp.write('\ufeff')
        w = csv.writer(resp)
        w.writerow(['Taux TVA', 'Base HT client', 'TVA collectée', 'Base HT fournisseur', 'TVA déductible'])
        for rate in sorted(all_rates.keys()):
            r = all_rates[rate]
            w.writerow([f'{rate}%', round(r['ht_client'], 2), round(r['tva_client'], 2), round(r['ht_fourn'], 2), round(r['tva_fourn'], 2)])
        w.writerow([])
        w.writerow(['Total TVA collectée', '', round(total_tva_collectee, 2), '', ''])
        w.writerow(['Total TVA déductible', '', round(total_tva_deductible, 2), '', ''])
        w.writerow(['TVA nette à reverser', '', round(tva_net, 2), '', ''])
        return resp

    return render(request, 'erp/tva_report.html', {
        'rates': sorted_rates,
        'start': start, 'end': end,
        'total_tva_collectee': total_tva_collectee,
        'total_tva_deductible': total_tva_deductible,
        'tva_net': tva_net,
    })


# ─── Quotations ───────────────────────────────────────────────────

@login_required
def quotation_list(request):
    q_val = request.GET.get('q', '')
    s_val = request.GET.get('status', '')
    quotations = Quotation.objects.select_related('company', 'created_by').all()
    if q_val:
        quotations = quotations.filter(Q(number__icontains=q_val) | Q(company__name__icontains=q_val) | Q(notes__icontains=q_val))
    if s_val:
        quotations = quotations.filter(status=s_val)
    paginator = Paginator(quotations, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/quotation_list.html', {'quotations': page, 'q': q_val, 'filter_status': s_val, 'status_choices': Quotation.STATUS_CHOICES})


@login_required
def quotation_detail(request, pk):
    q = get_object_or_404(Quotation.objects.select_related('company', 'contact', 'created_by'), pk=pk)
    invoices = q.invoices.all()
    return render(request, 'erp/quotation_detail.html', {'q': q, 'invoices': invoices, 'vat_bd': vat_breakdown(q.lines)})


@login_required
def quotation_pdf(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    html = render(request, 'erp/pdf_document.html', {'doc': q, 'doc_type': 'Devis', 'show_payments': False}).content.decode('utf-8')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{q.number}.pdf"'
    HTML(string=html).write_pdf(response)
    return response


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
        log_audit(request, 'devis', q.pk, q.number, 'create', f'Création statut={q.status}')
        messages.success(request, f'Devis {q.number} créé.')
        return redirect('erp_quotation_detail', pk=q.pk)
    companies = Company.objects.all()
    return render(request, 'erp/quotation_form.html', {'quotation': None, 'companies': companies, 'status_choices': Quotation.STATUS_CHOICES, 'products': Product.objects.all()})


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
        old_status = q.status
        q.company_id = request.POST.get('company') or None
        q.contact_id = request.POST.get('contact') or None
        q.valid_until = request.POST.get('valid_until') or None
        q.status = request.POST.get('status', 'brouillon')
        q.lines = lines
        q.notes = request.POST.get('notes', '')
        q.save()
        log_audit(request, 'devis', q.pk, q.number, 'edit', f'Statut: {old_status}→{q.status}')
        if old_status != 'accepte' and q.status == 'accepte':
            notify_admins(
                f'Devis accepté : {q.number}',
                f'Le devis {q.number} pour {q.company} a été accepté (montant TTC : {q.total_ttc()} €).',
                link=f'/erp/devis/{q.pk}/',
            )
        messages.success(request, f'Devis {q.number} modifié.')
        return redirect('erp_quotation_detail', pk=q.pk)
    companies = Company.objects.all()
    return render(request, 'erp/quotation_form.html', {'quotation': q, 'companies': companies, 'status_choices': Quotation.STATUS_CHOICES, 'products': Product.objects.all()})


@login_required
def quotation_delete(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        log_audit(request, 'devis', q.pk, q.number, 'delete')
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
    log_audit(request, 'devis', q.pk, q.number, 'convert', f'Converti en facture {inv.number}')
    log_audit(request, 'facture', inv.pk, inv.number, 'create', f'Issu du devis {q.number}')
    notify_admins(
        f'Facture créée : {inv.number}',
        f'La facture {inv.number} a été créée depuis le devis {q.number} (montant TTC : {inv.total_ttc()} €).',
        link=f'/erp/factures/{inv.pk}/',
    )
    messages.success(request, f'Facture {inv.number} créée depuis le devis {q.number}.')
    return redirect('erp_invoice_detail', pk=inv.pk)


# ─── Invoices ──────────────────────────────────────────────────────

@login_required
def invoice_list(request):
    q_val = request.GET.get('q', '')
    s_val = request.GET.get('status', '')
    invoices = Invoice.objects.select_related('company', 'created_by').all()
    if q_val:
        invoices = invoices.filter(Q(number__icontains=q_val) | Q(company__name__icontains=q_val) | Q(notes__icontains=q_val))
    if s_val:
        invoices = invoices.filter(status=s_val)
    paginator = Paginator(invoices, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/invoice_list.html', {'invoices': page, 'q': q_val, 'filter_status': s_val, 'status_choices': Invoice.STATUS_CHOICES})


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related('company', 'contact', 'quotation', 'created_by'), pk=pk)
    payments = inv.payments.all()
    credit_notes = inv.credit_notes.all()
    return render(request, 'erp/invoice_detail.html', {'inv': inv, 'payments': payments, 'credit_notes': credit_notes, 'vat_bd': vat_breakdown(inv.lines)})


@login_required
def invoice_pdf(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related('company', 'contact'), pk=pk)
    html = render(request, 'erp/pdf_document.html', {'doc': inv, 'doc_type': 'Facture', 'show_payments': True}).content.decode('utf-8')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{inv.number}.pdf"'
    HTML(string=html).write_pdf(response)
    return response


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
        log_audit(request, 'facture', inv.pk, inv.number, 'create', f'Création statut={inv.status}')
        messages.success(request, f'Facture {inv.number} créée.')
        return redirect('erp_invoice_detail', pk=inv.pk)
    companies = Company.objects.all()
    return render(request, 'erp/invoice_form.html', {'invoice': None, 'companies': companies, 'status_choices': Invoice.STATUS_CHOICES, 'products': Product.objects.all()})


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
        old_status = inv.status
        inv.company_id = request.POST.get('company') or None
        inv.contact_id = request.POST.get('contact') or None
        inv.due_date = request.POST.get('due_date') or None
        inv.status = request.POST.get('status', 'brouillon')
        inv.lines = lines
        inv.notes = request.POST.get('notes', '')
        inv.save()
        log_audit(request, 'facture', inv.pk, inv.number, 'edit', f'Statut: {old_status}→{inv.status}')
        messages.success(request, f'Facture {inv.number} modifiée.')
        return redirect('erp_invoice_detail', pk=inv.pk)
    companies = Company.objects.all()
    return render(request, 'erp/invoice_form.html', {'invoice': inv, 'companies': companies, 'status_choices': Invoice.STATUS_CHOICES, 'products': Product.objects.all()})


@login_required
def invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        log_audit(request, 'facture', inv.pk, inv.number, 'delete')
        inv.delete()
        messages.success(request, 'Facture supprimée.')
        return redirect('erp_invoice_list')
    return render(request, 'erp/confirm_delete.html', {'obj': inv})


# ─── Credit Notes ─────────────────────────────────────────────────

@login_required
def creditnote_list(request):
    q_val = request.GET.get('q', '')
    notes = CreditNote.objects.select_related('company', 'invoice', 'created_by').all()
    if q_val:
        notes = notes.filter(Q(number__icontains=q_val) | Q(company__name__icontains=q_val) | Q(reason__icontains=q_val))
    paginator = Paginator(notes, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/creditnote_list.html', {'notes': page, 'q': q_val})


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
        log_audit(request, 'avoir', cn.pk, cn.number, 'create', f'Motif: {cn.reason[:100]}')
        messages.success(request, f'Avoir {cn.number} créé.')
        return redirect('erp_creditnote_list')
    companies = Company.objects.all()
    invoices = Invoice.objects.all()
    return render(request, 'erp/creditnote_form.html', {'note': None, 'companies': companies, 'invoices': invoices, 'products': Product.objects.all()})


@login_required
def creditnote_delete(request, pk):
    cn = get_object_or_404(CreditNote, pk=pk)
    if request.method == 'POST':
        log_audit(request, 'avoir', cn.pk, cn.number, 'delete')
        cn.delete()
        messages.success(request, 'Avoir supprimé.')
        return redirect('erp_creditnote_list')
    return render(request, 'erp/confirm_delete.html', {'obj': cn})


# ─── Supplier Invoices ────────────────────────────────────────────

@login_required
def supplier_invoice_list(request):
    q_val = request.GET.get('q', '')
    s_val = request.GET.get('status', '')
    invoices = SupplierInvoice.objects.select_related('provider', 'created_by').all()
    if q_val:
        invoices = invoices.filter(Q(internal_number__icontains=q_val) | Q(number__icontains=q_val) | Q(provider__name__icontains=q_val) | Q(notes__icontains=q_val))
    if s_val:
        invoices = invoices.filter(status=s_val)
    paginator = Paginator(invoices, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/supplier_invoice_list.html', {'invoices': page, 'q': q_val, 'filter_status': s_val, 'status_choices': SupplierInvoice.STATUS_CHOICES})


# ─── Exports CSV ──────────────────────────────────────────────────

def _csv_response(filename):
    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    return response, csv.writer(response)


@login_required
def export_quotations_csv(request):
    resp, writer = _csv_response('devis.csv')
    writer.writerow(['N°', 'Société', 'Date', 'Total HT', 'TVA', 'Total TTC', 'Statut'])
    for q in Quotation.objects.select_related('company').all():
        writer.writerow([q.number, str(q.company or ''), str(q.date), q.total_ht(), q.total_tva(), q.total_ttc(), q.get_status_display()])
    return resp


@login_required
def export_invoices_csv(request):
    resp, writer = _csv_response('factures.csv')
    writer.writerow(['N°', 'Société', 'Date', 'Échéance', 'Total HT', 'TVA', 'Total TTC', 'Payé', 'Reste', 'Statut'])
    for inv in Invoice.objects.select_related('company').all():
        writer.writerow([inv.number, str(inv.company or ''), str(inv.date), str(inv.due_date or ''), inv.total_ht(), inv.total_tva(), inv.total_ttc(), inv.paid_amount, inv.remaining(), inv.get_status_display()])
    return resp


@login_required
def export_creditnotes_csv(request):
    resp, writer = _csv_response('avoirs.csv')
    writer.writerow(['N°', 'Société', 'Facture liée', 'Date', 'Total TTC', 'Motif'])
    for n in CreditNote.objects.select_related('company', 'invoice').all():
        writer.writerow([n.number, str(n.company or ''), n.invoice.number if n.invoice else '', str(n.date), n.total_ttc(), n.reason])
    return resp


@login_required
def export_supplier_invoices_csv(request):
    resp, writer = _csv_response('factures-fournisseurs.csv')
    writer.writerow(['N° interne', 'N° fournisseur', 'Fournisseur', 'Date', 'Échéance', 'Total TTC', 'Payé', 'Reste', 'Statut'])
    for inv in SupplierInvoice.objects.select_related('provider').all():
        writer.writerow([inv.internal_number, inv.number, str(inv.provider or ''), str(inv.date), str(inv.due_date or ''), inv.total_ttc(), inv.paid_amount, inv.remaining(), inv.get_status_display()])
    return resp


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
        log_audit(request, 'facture_fournisseur', inv.pk, inv.internal_number, 'create', f'Fournisseur: {inv.provider}')
        messages.success(request, f'Facture fournisseur {inv.internal_number} créée.')
        return redirect('erp_supplier_invoice_list')
    from apps.budget.providers.models import Provider
    providers = Provider.objects.all()
    return render(request, 'erp/supplier_invoice_form.html', {'invoice': None, 'providers': providers, 'status_choices': SupplierInvoice.STATUS_CHOICES, 'products': Product.objects.all()})


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
        log_audit(request, 'facture_fournisseur', inv.pk, inv.internal_number, 'edit', f'Statut: {inv.status}')
        messages.success(request, f'Facture fournisseur {inv.internal_number} modifiée.')
        return redirect('erp_supplier_invoice_list')
    from apps.budget.providers.models import Provider
    providers = Provider.objects.all()
    return render(request, 'erp/supplier_invoice_form.html', {'invoice': inv, 'providers': providers, 'status_choices': SupplierInvoice.STATUS_CHOICES, 'products': Product.objects.all()})


@login_required
def supplier_invoice_delete(request, pk):
    inv = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        log_audit(request, 'facture_fournisseur', inv.pk, inv.internal_number, 'delete')
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
            notify_admins(
                f'Paiement reçu — {p.invoice.number}',
                f'Paiement de {p.amount} € enregistré sur {p.invoice.number} (total payé : {total_paid} € / {p.invoice.total_ttc()} €).',
                link=f'/erp/factures/{p.invoice.pk}/',
            )
        if p.supplier_invoice:
            total_paid = p.supplier_invoice.payments.aggregate(Sum('amount'))['amount__sum'] or 0
            p.supplier_invoice.paid_amount = total_paid
            if total_paid >= p.supplier_invoice.total_ttc():
                p.supplier_invoice.status = 'payee'
            elif total_paid > 0:
                p.supplier_invoice.status = 'enregistree'
            p.supplier_invoice.save()
        ref = p.invoice.number if p.invoice else p.supplier_invoice.internal_number if p.supplier_invoice else 'N/A'
        log_audit(request, 'paiement', p.pk, f'{ref} — {p.amount}€', 'payment', f'Mode: {p.get_method_display()}')
        messages.success(request, 'Paiement enregistré.')
        return redirect('erp_dashboard')
    invoices = Invoice.objects.filter(status__in=['emise', 'impayee'])
    supplier_invoices = SupplierInvoice.objects.filter(status='enregistree')
    return render(request, 'erp/payment_form.html', {
        'invoices': invoices, 'supplier_invoices': supplier_invoices,
    })


# ─── Rélances ──────────────────────────────────────────────────────

@login_required
def reminder_list(request):
    overdue = Invoice.objects.filter(status__in=['emise', 'impayee'], due_date__lt=timezone.now().date())
    data = []
    for inv in overdue:
        last_reminder = inv.reminders.order_by('-level').first()
        data.append({
            'invoice': inv,
            'days_overdue': (timezone.now().date() - inv.due_date).days,
            'last_level': last_reminder.level if last_reminder else 0,
        })
    return render(request, 'erp/reminder_list.html', {'data': data})


@login_required
def reminder_create(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if inv.status not in ['emise', 'impayee'] or not inv.due_date or inv.due_date >= timezone.now().date():
        messages.error(request, 'Cette facture n\'est pas échue.')
        return redirect('erp_reminder_list')
    last = inv.reminders.order_by('-level').first()
    level = (last.level + 1) if last else 1
    if level > 3:
        messages.warning(request, '3 relances déjà envoyées pour cette facture.')
        return redirect('erp_reminder_list')
    Reminder.objects.create(
        invoice=inv,
        level=level,
        amount_due=inv.remaining(),
        created_by=request.user,
    )
    log_audit(request, 'relance', inv.pk, f'{inv.number} niveau {level}', 'reminder', f'Montant dû: {inv.remaining()} €')
    notify_admins(
        f'Relance niveau {level} — {inv.number}',
        f'La facture {inv.number} ({inv.company}) est impayée depuis {inv.due_date}. Montant dû : {inv.remaining()} €.',
        link=f'/erp/relances/{inv.pk}/',
    )
    messages.success(request, f'Relance niveau {level} générée pour {inv.number}.')
    return redirect('erp_reminder_detail', pk=inv.pk)


@login_required
def reminder_detail(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related('company'), pk=pk)
    reminders = inv.reminders.order_by('-level')
    return render(request, 'erp/reminder_detail.html', {'inv': inv, 'reminders': reminders})


@login_required
def reminder_pdf(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related('company', 'contact'), pk=pk)
    last = inv.reminders.order_by('-level').first()
    if not last:
        messages.error(request, 'Aucune relance pour cette facture.')
        return redirect('erp_reminder_list')
    html = render(request, 'erp/pdf_reminder.html', {'inv': inv, 'reminder': last}).content.decode('utf-8')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relance_{inv.number}_niveau{last.level}.pdf"'
    HTML(string=html).write_pdf(response)
    return response


# ─── Product catalogue ─────────────────────────────────────────────

@login_required
def product_list(request):
    q_val = request.GET.get('q', '')
    products = Product.objects.all()
    if q_val:
        products = products.filter(Q(name__icontains=q_val) | Q(category__icontains=q_val) | Q(description__icontains=q_val))
    paginator = Paginator(products, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/product_list.html', {'products': page, 'q': q_val})


@login_required
def product_create(request):
    if request.method == 'POST':
        p = Product.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            unit_price=request.POST['unit_price'],
            vat_rate=request.POST.get('vat_rate', 20),
            category=request.POST.get('category', ''),
            created_by=request.user,
        )
        log_audit(request, 'produit', p.pk, p.name, 'create', f'PU: {p.unit_price}€, TVA: {p.vat_rate}%')
        messages.success(request, 'Produit ajouté au catalogue.')
        return redirect('erp_product_list')
    return render(request, 'erp/product_form.html', {'product': None})


@login_required
def product_edit(request, pk):
    p = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        p.name = request.POST['name']
        p.description = request.POST.get('description', '')
        p.unit_price = request.POST['unit_price']
        p.vat_rate = request.POST.get('vat_rate', 20)
        p.category = request.POST.get('category', '')
        p.save()
        log_audit(request, 'produit', p.pk, p.name, 'edit', f'PU: {p.unit_price}€, Catégorie: {p.category}')
        messages.success(request, 'Produit modifié.')
        return redirect('erp_product_list')
    return render(request, 'erp/product_form.html', {'product': p})


# ─── Audit log ─────────────────────────────────────────────────────

@login_required
def audit_log_list(request):
    q = request.GET.get('q', '')
    model = request.GET.get('model', '')
    action = request.GET.get('action', '')
    logs = ErpAuditLog.objects.select_related('user').all()
    if q:
        logs = logs.filter(Q(object_repr__icontains=q) | Q(details__icontains=q))
    if model:
        logs = logs.filter(model_name=model)
    if action:
        logs = logs.filter(action=action)
    paginator = Paginator(logs, 50)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'erp/audit_log_list.html', {
        'logs': page,
        'q': q,
        'filter_model': model,
        'filter_action': action,
        'model_choices': ['devis', 'facture', 'avoir', 'facture_fournisseur', 'paiement', 'relance', 'produit'],
        'action_choices': ErpAuditLog.ACTION_CHOICES,
    })


@login_required
def product_delete(request, pk):
    p = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        log_audit(request, 'produit', p.pk, p.name, 'delete')
        p.delete()
        messages.success(request, f'Produit "{p.name}" supprimé.')
        return redirect('erp_product_list')
    return render(request, 'erp/confirm_delete.html', {'obj': p})
