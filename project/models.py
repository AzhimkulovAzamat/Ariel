from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название проекта")
    vcs_base_link = models.URLField(verbose_name="Базовая ссылка репозитория")
    issue_tracker_link = models.URLField(verbose_name="Базовая ссылка на доску задач")
    project_manager = models.CharField(max_length=200, verbose_name='Проект менеджер', default='https://t.me/vlelik')
    play_console_link = models.URLField('Ссылка на Play Console', default='')
    firebase_dashboard_link = models.URLField('Ссылка на Firebase Dashboard', default='')
    issue_dashboard_link = models.URLField('Ccылка на доску задач', default='')
    design_tools_link = models.URLField('Ccылка на макет дизайна', default='')
    backend_docs_link = models.URLField('Ccылка на документацию бека', default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Проекты"


class Access(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    git_token = models.TextField(verbose_name="Gitlab токен")
    issue_tracker_token = models.TextField(verbose_name="Jira токен")

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"

    class Meta:
        verbose_name_plural = "Доступы"
