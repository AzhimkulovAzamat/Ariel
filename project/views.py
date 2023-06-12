from rest_framework.views import APIView

from project.models import Access
from sevices.assistant.base_assistant import BaseAssistant
from sevices.issue_tracker.jira_service import JiraService
from sevices.vcs.gitlab_service import GitlabService


# Create your views here.
class GetMergeRequests(APIView):

    @staticmethod
    def get(request, project_id):
        access = Access.objects.get(project_id=project_id, user=request.user)

        gitlab = GitlabService(access.project, access)
        jira = JiraService(access.project, access)
        assistant = BaseAssistant(gitlab, jira)
        response = assistant.get_pull_requests()

        return response.to_drf_response(200)
