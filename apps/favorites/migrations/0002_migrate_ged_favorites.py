from django.db import migrations


def migrate_ged_favorites(apps, schema_editor):
    UserFavorite = apps.get_model('ged', 'UserFavorite')
    Favorite = apps.get_model('favorites', 'Favorite')
    count = 0
    for uf in UserFavorite.objects.select_related('document', 'user').all():
        fav, created = Favorite.objects.get_or_create(
            user=uf.user,
            content_type='ged.Document',
            object_id=uf.document_id,
            defaults={
                'label': f'{uf.document.title} (v{uf.document.version})',
                'module': 'GED',
                'url': f'/ged/{uf.document.pk}/',
            },
        )
        if created:
            count += 1
    print(f'Migrated {count} GED favorites to global favorites.')


def reverse_migrate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ged', '0001_initial'),
        ('favorites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_ged_favorites, reverse_migrate),
    ]
