from django.contrib import admin
from .models import Quotation, Invoice, CreditNote, SupplierInvoice, Payment

admin.site.register(Quotation)
admin.site.register(Invoice)
admin.site.register(CreditNote)
admin.site.register(SupplierInvoice)
admin.site.register(Payment)
