from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import secrets


class Role(models.Model):
    code = models.CharField(max_length=30, unique=True, verbose_name='Code')
    label = models.CharField(max_length=100, verbose_name='Libellé')

    class Meta:
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['code']

    def __str__(self):
        return self.label


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True, verbose_name='Rôles')
    two_factor_enabled = models.BooleanField(default=False, verbose_name='2FA activé')
    two_factor_secret = models.CharField(max_length=64, blank=True, verbose_name='Code 2FA')
    two_factor_created = models.DateTimeField(null=True, blank=True, verbose_name='Création 2FA')
    ldap_dn = models.CharField(max_length=512, blank=True, verbose_name='DN LDAP')

    def generate_2fa_code(self):
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        self.two_factor_secret = code
        self.two_factor_created = timezone.now()
        self.save(update_fields=['two_factor_secret', 'two_factor_created'])
        return code

    def verify_2fa_code(self, code):
        if not self.two_factor_secret or not self.two_factor_created:
            return False
        if (timezone.now() - self.two_factor_created).total_seconds() > 300:
            return False
        return self.two_factor_secret == code

    def __str__(self):
        roles = ', '.join(str(r) for r in self.roles.all()) or 'Aucun rôle'
        return f"{self.user.username} - {roles}"

    def is_admin(self):
        return self.roles.filter(code='admin').exists()

    def has_role(self, code):
        return self.roles.filter(code=code).exists()

    def can_write_blog(self, blog_type):
        user_codes = set(self.roles.values_list('code', flat=True))
        if 'admin' in user_codes:
            return True
        permissions = {
            'security': ['security_officer'],
            'direction': ['direction'],
            'communication': ['communication'],
            'it': ['direction'],
            'comex': ['direction'],
            'rep_syndicale': ['elus_syndicaux'],
        }
        return bool(user_codes & set(permissions.get(blog_type, [])))


class LdapConfig(models.Model):
    enabled = models.BooleanField(default=False, verbose_name='LDAP activé')
    server_uri = models.CharField(max_length=500, blank=True, verbose_name='URI serveur LDAP')
    bind_dn = models.CharField(max_length=500, blank=True, verbose_name='DN de liaison')
    bind_password = models.CharField(max_length=500, blank=True, verbose_name='Mot de passe liaison')
    base_dn = models.CharField(max_length=500, blank=True, verbose_name='DN base')
    user_filter = models.CharField(max_length=500, blank=True, default='(uid=%(user)s)', verbose_name='Filtre utilisateur')
    attribute_username = models.CharField(max_length=100, default='uid', verbose_name='Attribut username')
    attribute_email = models.CharField(max_length=100, default='mail', verbose_name='Attribut email')
    attribute_fullname = models.CharField(max_length=100, default='cn', verbose_name='Attribut nom complet')

    class Meta:
        verbose_name = 'Configuration LDAP'
        verbose_name_plural = 'Configuration LDAP'

    def __str__(self):
        return 'LDAP: ' + ('Activé' if self.enabled else 'Désactivé')
