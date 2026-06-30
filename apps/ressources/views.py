from django.shortcuts import render
from django.contrib.auth.decorators import login_required


RESSOURCES = [
    {
        'id': 'rgpd',
        'title': 'RGPD',
        'subtitle': 'Règlement Général sur la Protection des Données',
        'description': 'Règlement européen encadrant la collecte et le traitement des données personnelles des citoyens de l\'UE.',
        'color': 'from-blue-600 to-blue-800',
        'icon': '🛡️',
    },
    {
        'id': 'igi_1300',
        'title': 'IGI 1300',
        'subtitle': 'Instruction Générale Interministérielle n°1300',
        'description': 'Protection du secret de la défense nationale dans les systèmes d\'information classifiés.',
        'color': 'from-red-700 to-red-900',
        'icon': '🔒',
    },
    {
        'id': 'im_900',
        'title': 'IM 900',
        'subtitle': 'Instruction Ministérielle n°900',
        'description': 'Protection du secret et des informations diffusion restreinte et sensibles au ministère des Armées.',
        'color': 'from-amber-600 to-amber-800',
        'icon': '📜',
    },
    {
        'id': 'ii_901',
        'title': 'II 901',
        'subtitle': 'Instruction Interministérielle n°901',
        'description': 'Protection des systèmes d\'information sensibles et des données Diffusion Restreinte.',
        'color': 'from-emerald-600 to-emerald-800',
        'icon': '🔐',
    },
    {
        'id': 'pci_dss',
        'title': 'PCI DSS',
        'subtitle': 'Payment Card Industry Data Security Standard',
        'description': 'Standard de sécurité des données de l\'industrie des cartes de paiement.',
        'color': 'from-purple-600 to-purple-800',
        'icon': '💳',
    },
    {
        'id': 'nis',
        'title': 'NIS 2',
        'subtitle': 'Network and Information Security Directive',
        'description': 'Directive européenne sur la sécurité des réseaux et des systèmes d\'information.',
        'color': 'from-cyan-600 to-cyan-800',
        'icon': '🌐',
    },
    {
        'id': 'ebios_rm',
        'title': 'EBIOS RM',
        'subtitle': 'Expression des Besoins et Identification des Objectifs de Sécurité — Risk Manager',
        'description': 'Méthode française d\'analyse des risques SSI, référentiel de l\'ANSSI.',
        'color': 'from-rose-600 to-rose-800',
        'icon': '📊',
    },
    {
        'id': 'iec_62443',
        'title': 'IEC 62443',
        'subtitle': 'Industrial Communication Networks — Network and System Security',
        'description': 'Série de normes internationales pour la cybersécurité des systèmes industriels et ICS.',
        'color': 'from-teal-600 to-teal-800',
        'icon': '🏭',
    },
    {
        'id': 'iso_27001',
        'title': 'ISO 27001',
        'subtitle': 'Information Security Management System (ISMS)',
        'description': 'Norme internationale pour le management de la sécurité de l\'information (SMSI).',
        'color': 'from-sky-600 to-sky-800',
        'icon': '✅',
    },
    {
        'id': 'iso_27032',
        'title': 'ISO 27032',
        'subtitle': 'Guidelines for Cybersecurity',
        'description': 'Lignes directrices internationales pour la cybersécurité et la coordination interne/externe.',
        'color': 'from-violet-600 to-violet-800',
        'icon': '🌍',
    },
]


@login_required
def home(request):
    return render(request, 'ressources/home.html', {'ressources': RESSOURCES})


@login_required
def rgpd(request):
    return render(request, 'ressources/rgpd.html')


@login_required
def igi_1300(request):
    return render(request, 'ressources/igi_1300.html')


@login_required
def im_900(request):
    return render(request, 'ressources/im_900.html')


@login_required
def ii_901(request):
    return render(request, 'ressources/ii_901.html')


@login_required
def pci_dss(request):
    return render(request, 'ressources/pci_dss.html')


@login_required
def nis(request):
    return render(request, 'ressources/nis.html')


@login_required
def ebios_rm(request):
    return render(request, 'ressources/ebios_rm.html')


@login_required
def iec_62443(request):
    return render(request, 'ressources/iec_62443.html')


@login_required
def iso_27001(request):
    return render(request, 'ressources/iso_27001.html')


@login_required
def iso_27032(request):
    return render(request, 'ressources/iso_27032.html')
