from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(max_length=100, verbose_name='Type')),
                ('object_id', models.PositiveIntegerField(verbose_name='ID')),
                ('label', models.CharField(max_length=300, verbose_name='Libellé')),
                ('module', models.CharField(max_length=50, verbose_name='Module')),
                ('url', models.CharField(max_length=500, verbose_name='URL')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ajouté le')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Favori',
                'verbose_name_plural': 'Favoris',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'content_type', 'object_id')},
            },
        ),
    ]
