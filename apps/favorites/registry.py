from django.urls import reverse


REGISTRY = {
    'crm.Company': {
        'module': 'CRM',
        'label_attr': 'name',
        'url': lambda obj: reverse('crm_company_detail', args=[obj.pk]),
    },
    'crm.Contact': {
        'module': 'CRM',
        'label': lambda obj: f'{obj.first_name} {obj.last_name}',
        'url': lambda obj: reverse('crm_contact_list'),
    },
    'crm.Deal': {
        'module': 'CRM',
        'label_attr': 'title',
        'url': lambda obj: reverse('crm_deal_detail', args=[obj.pk]),
    },
    'erp.Quotation': {
        'module': 'ERP',
        'label_attr': 'number',
        'url': lambda obj: reverse('erp_quotation_detail', args=[obj.pk]),
    },
    'erp.Invoice': {
        'module': 'ERP',
        'label_attr': 'number',
        'url': lambda obj: reverse('erp_invoice_detail', args=[obj.pk]),
    },
    'erp.CreditNote': {
        'module': 'ERP',
        'label_attr': 'number',
        'url': lambda obj: reverse('erp_creditnote_list'),
    },
    'erp.SupplierInvoice': {
        'module': 'ERP',
        'label_attr': 'internal_number',
        'url': lambda obj: reverse('erp_supplier_invoice_list'),
    },
    'projects.Project': {
        'module': 'ALM',
        'label_attr': 'name',
        'url': lambda obj: reverse('project_detail', args=[obj.pk]),
    },
    'tickets.Ticket': {
        'module': 'ALM',
        'label': lambda obj: f'{obj.get_formatted_number()} - {obj.title}',
        'url': lambda obj: reverse('ticket_detail', args=[obj.project_id, obj.pk]),
    },
    'requirements.Requirement': {
        'module': 'ALM',
        'label': lambda obj: f'{obj.get_formatted_number()} - {obj.name}',
        'url': lambda obj: reverse('requirement_detail', args=[obj.project_id, obj.pk]),
    },
    'tests.TestCampaign': {
        'module': 'ALM',
        'label_attr': 'name',
        'url': lambda obj: reverse('campaign_detail', args=[obj.project_id, obj.pk]),
    },
    'ged.Document': {
        'module': 'GED',
        'label': lambda obj: f'{obj.title} (v{obj.version})',
        'url': lambda obj: reverse('ged_document_detail', args=[obj.pk]),
    },
    'wiki.WikiPage': {
        'module': 'Wiki',
        'label_attr': 'title',
        'url': lambda obj: reverse('wiki_detail', args=[obj.slug]),
    },
    'dat.DAT': {
        'module': 'Budget',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('dat_detail', args=[obj.pk]),
    },
    'guichet.GuichetTicket': {
        'module': 'Guichet',
        'label': lambda obj: f'{obj.get_formatted_number()} - {obj.title}',
        'url': lambda obj: reverse('guichet_detail', args=[obj.pk]),
    },
    'sec_blog.SecurityArticle': {
        'module': 'Blog',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('sec_blog_detail', args=[obj.pk]),
    },
    'dg_blog.DirectionArticle': {
        'module': 'Blog',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('dg_blog_detail', args=[obj.pk]),
    },
    'blog_com.ComArticle': {
        'module': 'Blog',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('com_blog_detail', args=[obj.pk]),
    },
    'blog_it.ITArticle': {
        'module': 'Blog',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('it_blog_detail', args=[obj.pk]),
    },
    'blog_rep.RepSyndicaleArticle': {
        'module': 'Blog',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('rep_syndicale_blog_detail', args=[obj.pk]),
    },
    'comex_forum.ComexThread': {
        'module': 'COMEX',
        'label': lambda obj: obj.display_id(),
        'url': lambda obj: reverse('comex_thread_detail', args=[obj.pk]),
    },
}


def get_label(obj):
    model_key = f'{obj._meta.app_label}.{obj.__class__.__name__}'
    entry = REGISTRY.get(model_key)
    if not entry:
        return str(obj)
    if 'label' in entry:
        return entry['label'](obj)
    return getattr(obj, entry.get('label_attr', '__str__'), str(obj))


def get_url(obj):
    model_key = f'{obj._meta.app_label}.{obj.__class__.__name__}'
    entry = REGISTRY.get(model_key)
    if not entry:
        return '#'
    return entry['url'](obj)


def get_module(obj):
    model_key = f'{obj._meta.app_label}.{obj.__class__.__name__}'
    entry = REGISTRY.get(model_key)
    return entry['module'] if entry else 'Autre'
