from django.contrib import admin
from .models import DocumentCategory, Document, UserFavorite, CategorySubscription, AuditLog

admin.site.register(DocumentCategory)
admin.site.register(Document)
admin.site.register(UserFavorite)
admin.site.register(CategorySubscription)
admin.site.register(AuditLog)
