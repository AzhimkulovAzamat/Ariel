# Generated by Django 4.2.2 on 2023-06-14 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0003_project_play_console_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='backend_docs_link',
            field=models.URLField(default='', verbose_name='Ccылка на документацию бека'),
        ),
        migrations.AddField(
            model_name='project',
            name='design_tools_link',
            field=models.URLField(default='', verbose_name='Ccылка на макет дизайна'),
        ),
        migrations.AddField(
            model_name='project',
            name='firebase_dashboard_link',
            field=models.URLField(default='', verbose_name='Ссылка на Firebase Dashboard'),
        ),
        migrations.AddField(
            model_name='project',
            name='issue_dashboard_link',
            field=models.URLField(default='', verbose_name='Ccылка на доску задач'),
        ),
    ]
