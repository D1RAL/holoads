# Generated by Django 5.2 on 2025-05-17 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='media/')),
                ('media_type', models.CharField(choices=[('video', 'Vidéo'), ('image', 'Image')], max_length=10)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Video',
        ),
    ]
