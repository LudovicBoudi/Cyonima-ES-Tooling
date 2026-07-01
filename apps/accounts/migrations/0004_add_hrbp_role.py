from django.db import migrations


def seed_hrbp(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.get_or_create(code='hrbp', defaults={'label': 'HR Business Partner'})


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_multi_role'),
    ]

    operations = [
        migrations.RunPython(seed_hrbp),
    ]
