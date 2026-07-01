from django.db import migrations


def seed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('ged', 'DocumentCategory')
    categories = [
        ('Ressources Humaines', '#e63946'),
        ('Juridique & Conformité', '#1d3557'),
        ('Finances & Comptabilité', '#2a9d8f'),
        ('Informatique & Technique', '#264653'),
        ('Commercial & Marketing', '#e76f51'),
        ('Procédures & Processus', '#f4a261'),
        ('Formation & Compétences', '#e9c46a'),
        ('Qualité & Sécurité', '#457b9d'),
        ('Direction & Stratégie', '#6a4c93'),
        ('Projets & Affaires', '#ffb703'),
        ('Communication & Externe', '#fb8500'),
    ]
    for name, color in categories:
        DocumentCategory.objects.get_or_create(name=name, defaults={'color': color})


class Migration(migrations.Migration):

    dependencies = [
        ('ged', '0002_document_registration_number'),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
