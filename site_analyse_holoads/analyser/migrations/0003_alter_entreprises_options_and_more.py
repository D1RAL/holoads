# Generated by Django 5.2 on 2025-05-25 04:19

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyser', '0002_alter_entreprises_options_entreprises_video_path'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entreprises',
            options={'verbose_name': 'Entreprise analysée', 'verbose_name_plural': 'Entreprises analysées'},
        ),
        migrations.RemoveField(
            model_name='entreprises',
            name='date_creation',
        ),
        migrations.AddField(
            model_name='entreprises',
            name='analyzed_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name="Date d'analyse"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entreprises',
            name='video_id_reference',
            field=models.IntegerField(blank=True, null=True, verbose_name="ID de référence dans l'app videos"),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='adresse',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='domaine',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='entreprise',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='telephone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='entreprises',
            name='video_path',
            field=models.CharField(blank=True, default='', max_length=500),
            preserve_default=False,
        ),
    ]
