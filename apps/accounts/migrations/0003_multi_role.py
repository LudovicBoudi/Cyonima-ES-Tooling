from django.db import migrations, models


ROLES = [
    ('admin', 'Administrateur'),
    ('it_manager', 'Gestionnaire IT'),
    ('controller', 'Contrôleur de gestion'),
    ('security_officer', 'Officier de sécurité'),
    ('direction', 'Direction générale'),
    ('communication', 'Communication'),
    ('user', 'Utilisateur'),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    for code, label in ROLES:
        Role.objects.get_or_create(code=code, defaults={'label': label})


def migrate_old_roles(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Role = apps.get_model('accounts', 'Role')
    for profile in UserProfile.objects.all():
        old_role = getattr(profile, 'role', None) or 'user'
        try:
            role = Role.objects.get(code=old_role)
            if not profile.roles.filter(pk=role.pk).exists():
                profile.roles.add(role)
        except Role.DoesNotExist:
            role, _ = Role.objects.get_or_create(code='user', defaults={'label': 'Utilisateur'})
            if not profile.roles.filter(pk=role.pk).exists():
                profile.roles.add(role)


def add_admin_roles(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Role = apps.get_model('accounts', 'Role')
    User = apps.get_model('auth', 'User')
    try:
        admin_user = User.objects.get(username='admin')
        profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        existing = set(profile.roles.values_list('code', flat=True))
        for role in Role.objects.filter(code__in=['admin', 'it_manager']):
            if role.code not in existing:
                profile.roles.add(role)
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_ldapconfig_userprofile_ldap_dn_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True, verbose_name='Code')),
                ('label', models.CharField(max_length=100, verbose_name='Libellé')),
            ],
            options={
                'verbose_name': 'Rôle',
                'verbose_name_plural': 'Rôles',
                'ordering': ['code'],
            },
        ),
        migrations.RunPython(seed_roles),
        migrations.AddField(
            model_name='userprofile',
            name='roles',
            field=models.ManyToManyField(blank=True, to='accounts.Role', verbose_name='Rôles'),
        ),
        migrations.RunPython(migrate_old_roles),
        migrations.RemoveField(
            model_name='userprofile',
            name='role',
        ),
        migrations.RunPython(add_admin_roles),
    ]
