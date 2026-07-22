import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.crm.models import Contact


class PortalUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portal_profile')
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='portal_user')
    token = models.UUIDField('Token', default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField('Actif', default=False)
    invited_at = models.DateTimeField('Invité le', auto_now_add=True)
    activated_at = models.DateTimeField('Activé le', null=True, blank=True)

    class Meta:
        verbose_name = 'Utilisateur portail'
        verbose_name_plural = 'Utilisateurs portail'

    def __str__(self):
        return f'{self.contact} ({self.user.username})'
