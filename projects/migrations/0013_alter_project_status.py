# Generated by Django 5.1.6 on 2025-02-12 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_alter_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('ON_HOLD', 'Em Pausa'), ('IN_PROGRESS', 'Em Andamento'), ('COMPLETED', 'Concluído'), ('PLANNING', 'Em Planejamento')], default='PLANNING', help_text='Status atual do projeto (Planejamento, Em Andamento, Concluído ou Em Pausa)', max_length=20),
        ),
    ]
