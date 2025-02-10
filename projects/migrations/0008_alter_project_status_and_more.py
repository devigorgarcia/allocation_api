# Generated by Django 5.1.6 on 2025-02-10 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_alter_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('COMPLETED', 'Concluído'), ('PLANNING', 'Em Planejamento'), ('IN_PROGRESS', 'Em Andamento'), ('ON_HOLD', 'Em Pausa')], default='PLANNING', help_text='Status atual do projeto (Planejamento, Em Andamento, Concluído ou Em Pausa)', max_length=20),
        ),
        migrations.AlterField(
            model_name='projectdeveloper',
            name='hours_per_month',
            field=models.PositiveIntegerField(default=0, help_text='Quantidade de horas mensais que o desenvolvedor dedicará ao projeto', verbose_name='Horas por mês'),
        ),
    ]
