from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from weasyprint import HTML

from .models import PortalUser
from .decorators import portal_required
from .forms import PortalLoginForm, PortalActivationForm
from apps.erp.models import Quotation, Invoice, CreditNote


def portal_login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('portal:dashboard')
    form = PortalLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is not None and not user.is_staff:
            login(request, user)
            return redirect('portal:dashboard')
        messages.error(request, 'Identifiants incorrects ou accès non autorisé.')
    return render(request, 'portal/login.html', {'form': form})


def portal_logout(request):
    logout(request)
    return redirect('portal:login')


def portal_activate(request, token):
    portal_user = get_object_or_404(PortalUser, token=token, is_active=False)
    if request.method == 'POST':
        form = PortalActivationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exclude(pk=portal_user.user.pk).exists():
                messages.error(request, 'Cet identifiant est déjà utilisé.')
            else:
                portal_user.user.username = username
                portal_user.user.set_password(form.cleaned_data['password1'])
                portal_user.user.save()
                portal_user.is_active = True
                portal_user.activated_at = timezone.now()
                portal_user.save()
                messages.success(request, 'Votre compte a été activé. Vous pouvez vous connecter.')
                return redirect('portal:login')
    else:
        form = PortalActivationForm(initial={'username': portal_user.user.username})
    return render(request, 'portal/activate.html', {'form': form, 'token': token})


@portal_required
def dashboard(request):
    contact = request.user.portal_profile.contact
    from apps.notifications.models import Notification
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    quotations = Quotation.objects.filter(contact=contact)
    invoices = Invoice.objects.filter(contact=contact)
    creditnotes = CreditNote.objects.filter(invoice__contact=contact)
    unpaid_invoices = invoices.filter(status__in=['emise', 'impayee'])
    overdue_invoices = unpaid_invoices.filter(due_date__lt=timezone.now().date())
    total_unpaid = sum(inv.remaining for inv in unpaid_invoices)
    return render(request, 'portal/dashboard.html', {
        'contact': contact,
        'company': contact.company,
        'quotations': quotations[:10],
        'invoices': invoices[:10],
        'creditnotes': creditnotes[:10],
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_unpaid': total_unpaid,
        'unpaid_count': unpaid_invoices.count(),
        'quotation_count': quotations.count(),
        'invoice_count': invoices.count(),
        'creditnote_count': creditnotes.count(),
        'unread_notifications_count': unread_count,
    })


@portal_required
def quotation_list(request):
    contact = request.user.portal_profile.contact
    quotations = Quotation.objects.filter(contact=contact).order_by('-date')
    paginator = Paginator(quotations, 25)
    page = request.GET.get('page')
    quotations_page = paginator.get_page(page)
    return render(request, 'portal/quotation_list.html', {'quotations': quotations_page})


@portal_required
def quotation_detail(request, pk):
    contact = request.user.portal_profile.contact
    quotation = get_object_or_404(Quotation, pk=pk, contact=contact)
    return render(request, 'portal/quotation_detail.html', {'quotation': quotation})


@portal_required
def quotation_pdf(request, pk):
    contact = request.user.portal_profile.contact
    quotation = get_object_or_404(Quotation, pk=pk, contact=contact)
    from apps.core.models import SiteConfig
    config = SiteConfig.objects.first()
    html_string = render_to_string('erp/pdf_document.html', {
        'doc': quotation, 'doc_type': 'Devis', 'show_payments': False,
        'site_config': config or {'site_name': 'Cyonima-ES-Tools', 'logo': None},
    })
    pdf = HTML(string=html_string).write_pdf()
    return FileResponse(pdf, content_type='application/pdf', filename=f'{quotation.number}.pdf')


@portal_required
def invoice_list(request):
    contact = request.user.portal_profile.contact
    invoices = Invoice.objects.filter(contact=contact).order_by('-date')
    paginator = Paginator(invoices, 25)
    page = request.GET.get('page')
    invoices_page = paginator.get_page(page)
    return render(request, 'portal/invoice_list.html', {
        'invoices': invoices_page,
        'today': timezone.now().date(),
    })


@portal_required
def invoice_detail(request, pk):
    contact = request.user.portal_profile.contact
    invoice = get_object_or_404(Invoice, pk=pk, contact=contact)
    payments = invoice.payments.all() if hasattr(invoice, 'payments') else []
    credit_notes = invoice.credit_notes.all() if hasattr(invoice, 'credit_notes') else []
    return render(request, 'portal/invoice_detail.html', {
        'invoice': invoice,
        'payments': payments,
        'credit_notes': credit_notes,
    })


@portal_required
def invoice_pdf(request, pk):
    contact = request.user.portal_profile.contact
    invoice = get_object_or_404(Invoice, pk=pk, contact=contact)
    from apps.core.models import SiteConfig
    config = SiteConfig.objects.first()
    html_string = render_to_string('erp/pdf_document.html', {
        'doc': invoice, 'doc_type': 'Facture', 'show_payments': True,
        'site_config': config or {'site_name': 'Cyonima-ES-Tools', 'logo': None},
    })
    pdf = HTML(string=html_string).write_pdf()
    return FileResponse(pdf, content_type='application/pdf', filename=f'{invoice.number}.pdf')


@portal_required
def creditnote_list(request):
    contact = request.user.portal_profile.contact
    creditnotes = CreditNote.objects.filter(invoice__contact=contact).order_by('-date')
    paginator = Paginator(creditnotes, 25)
    page = request.GET.get('page')
    creditnotes_page = paginator.get_page(page)
    return render(request, 'portal/creditnote_list.html', {'creditnotes': creditnotes_page})


@portal_required
def creditnote_detail(request, pk):
    contact = request.user.portal_profile.contact
    creditnote = get_object_or_404(CreditNote, pk=pk, invoice__contact=contact)
    return render(request, 'portal/creditnote_detail.html', {'creditnote': creditnote})


@portal_required
def creditnote_pdf(request, pk):
    contact = request.user.portal_profile.contact
    creditnote = get_object_or_404(CreditNote, pk=pk, invoice__contact=contact)
    from apps.core.models import SiteConfig
    config = SiteConfig.objects.first()
    html_string = render_to_string('erp/pdf_document.html', {
        'doc': creditnote, 'doc_type': 'Avoir', 'show_payments': False,
        'site_config': config or {'site_name': 'Cyonima-ES-Tools', 'logo': None},
    })
    pdf = HTML(string=html_string).write_pdf()
    return FileResponse(pdf, content_type='application/pdf', filename=f'{creditnote.number}.pdf')


@login_required(login_url='portal:login')
def portal_password_change(request):
    if request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe modifié avec succès.')
            return redirect('portal:dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'portal/password_change.html', {'form': form})


@portal_required
def portal_account(request):
    contact = request.user.portal_profile.contact
    return render(request, 'portal/mon_compte.html', {'contact': contact})
