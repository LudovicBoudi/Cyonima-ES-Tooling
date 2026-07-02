from django.contrib import admin
from .models import Product, Quotation, Invoice, CreditNote, SupplierInvoice, Payment, ErpAuditLog

admin.site.register(Product)
admin.site.register(Quotation)
admin.site.register(Invoice)
admin.site.register(CreditNote)
admin.site.register(SupplierInvoice)
admin.site.register(Payment)
admin.site.register(ErpAuditLog)
