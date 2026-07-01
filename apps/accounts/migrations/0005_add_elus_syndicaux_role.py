from django.db import migrations

def seed_elus_syndicaux(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.get_or_create(code='elus_syndicaux', defaults={'label': 'Élus Syndicaux'})

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_add_hrbp_role'),
    ]
    operations = [
        migrations.RunPython(seed_elus_syndicaux),
    ]
