# Generated by Django 5.1.6 on 2025-02-12 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0018_alter_project_options_alter_projectdeveloper_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('COMPLETED', 'Concluído'), ('IN_PROGRESS', 'Em Andamento'), ('ON_HOLD', 'Em Pausa'), ('PLANNING', 'Em Planejamento')], default='PLANNING', help_text='Status atual do projeto (Planejamento, Em Andamento, Concluído ou Em Pausa)', max_length=20),
        ),
    ]
