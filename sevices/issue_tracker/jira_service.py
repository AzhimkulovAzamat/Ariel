import re

import requests

from project.models import Project, Access
from sevices.issue_tracker.issue_tracker_protocol import IssueTrackerProtocol, IssueTrackerModel
from sevices.vcs.vcs_protocol import BaseResponse, VcsProtocol


class JiraService(IssueTrackerProtocol):

    def __init__(self, project: Project, access: Access):
        self.project = project
        self.access = access

    def get_issue_details(self, ticket_id) -> BaseResponse:
        headers = {'Authorization': f'Basic {self.access.issue_tracker_token}'}

        url = f"{self.project.issue_tracker_link}/rest/api/3/issue/{ticket_id}"
        response = requests.get(url, headers=headers)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_issue_details,
                                                 self._parse_error)

    def get_url_for_ticket(self, ticket_id) -> str:
        return f'{self.project.issue_tracker_link}/browse/{ticket_id}'

    def get_ticket_id_from_branch(self, name: str) -> str:
        return name.split("/")[-1]

    def format_title_for_vcs(self, ticket_id) -> str:
        response = self.get_issue_details(ticket_id)
        issue_title = response.data.title
        return f"{ticket_id.upper()} {issue_title}"

    def format_link_for_issue_in_vsc_description(self, ticket_id, vcs: VcsProtocol, title='Ссылка на Jira'):
        url_to_ticket = self.get_url_for_ticket(ticket_id)
        return f"[{title}]({url_to_ticket})"

    def get_beautified_logs(self, logs) -> str:
        id_pattern = re.compile(r"\((kdkapp-\d+)\)")
        name_pattern = re.compile(r"^(.*?)\s*\(")
        tickets = {}

        for line in logs.split("\n"):
            id_match_result = id_pattern.search(line)
            name_match_result = name_pattern.search(line)
            ids = id_match_result.group(1) if id_match_result else None
            names = name_match_result.group(1) if name_match_result else None

            if ids and names:
                tickets[ids] = names

        beautified_logs = "\n".join(
            f"[{value}]({self.get_url_for_ticket(key)})"
            for key, value in tickets.items()
        )

        return beautified_logs

    @staticmethod
    def _parse_issue_details(json) -> IssueTrackerModel:
        title = json.get('fields', {}).get('summary', 'Unresolved issue title')
        return IssueTrackerModel(title)

    @staticmethod
    def _parse_error(json) -> str:
        error_message = json.get('errorMessages', "Unresolved error")
        if isinstance(error_message, list):
            developer_error_message = error_message[0]
        else:
            developer_error_message = error_message
        return developer_error_message
