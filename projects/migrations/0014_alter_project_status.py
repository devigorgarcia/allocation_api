# Generated by Django 5.1.6 on 2025-02-12 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_alter_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('COMPLETED', 'Concluído'), ('ON_HOLD', 'Em Pausa'), ('PLANNING', 'Em Planejamento'), ('IN_PROGRESS', 'Em Andamento')], default='PLANNING', help_text='Status atual do projeto (Planejamento, Em Andamento, Concluído ou Em Pausa)', max_length=20),
        ),
    ]
