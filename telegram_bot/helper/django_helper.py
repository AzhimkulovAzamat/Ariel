from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, UserManager

from project.models import Project, Access
from telegram_bot.helper.sender import call_async


def get_user(username, password):
    user = authenticate(username=username, password=password)

    if user is not None:
        return user
    else:
        return None


async def get_project_from_user(user):
    projects = await sync_to_async(Project.objects.filter)(access__user=user)
    project_data = await sync_to_async(list)(
        projects.values('pk', 'name', 'vcs_base_link', 'issue_tracker_link', 'project_manager', 'play_console_link',
                        'firebase_dashboard_link', 'issue_dashboard_link', 'design_tools_link', 'backend_docs_link'))
    return project_data


async def get_user_by_telegram_user(id):
    get_user_by_last_name_sync = sync_to_async(User.objects.get)
    try:
        user = await get_user_by_last_name_sync(last_name=id)
        return user
    except UserManager.DoesNotExist:
        return None


async def get_access(user, project_id):
    access = await call_async(Access.objects.get, project_id=project_id, user=user)
    return access
