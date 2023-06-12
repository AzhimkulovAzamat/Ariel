import re

import requests

from sevices.assistant.assistant_protocol import AssistantProtocol
from sevices.issue_tracker.issue_tracker_protocol import IssueTrackerProtocol
from sevices.vcs.vcs_protocol import VcsProtocol, BaseResponse


class BaseAssistant(AssistantProtocol):

    def __init__(self, vcs_protocol: VcsProtocol, issue_tracker: IssueTrackerProtocol):
        self.vcs_protocol = vcs_protocol
        self.issue_tracker = issue_tracker

    def get_pull_requests(self, state: str = 'opened', source: str = None, target: str = None) -> BaseResponse:
        return self.vcs_protocol.get_pull_requests(state, source, target)

    def create_pull_request(self, title: str, description: str, source: str, target: str) -> BaseResponse:
        return self.vcs_protocol.create_pull_request(title, description, source, target)

    def create_developer_pull_request(self, source_branch) -> BaseResponse:
        return self._create_pul_request_to_exist_branch(source_branch, 'developer')

    def create_prerelease_pull_request(self, source_branch) -> BaseResponse:
        return self._create_pul_request_to_exist_branch(source_branch, 'release_prepare')

    def prepare_alpha(self) -> BaseResponse:
        return self._prepare_new_version('alpha', 'developer', 'alpha')

    def publish_beta(self) -> BaseResponse:
        return self._prepare_new_version('beta', 'alpha', 'beta')

    def publish_production(self) -> BaseResponse:
        return self._prepare_new_version('production', 'release_prepare', 'main')

    def check_branch_exists(self, branch_name: str) -> bool:
        return self.vcs_protocol.check_branch_exists(branch_name)

    def _create_pul_request_to_exist_branch(self, source_branch, target_branch) -> BaseResponse:
        ticket_id = self.issue_tracker.get_ticket_id_from_branch(source_branch)
        title = self.issue_tracker.format_title_for_vcs(ticket_id)
        description = self.issue_tracker.format_link_for_issue_in_vsc_description(ticket_id, self.vcs_protocol,
                                                                                  "Ссылка на Jira")

        return self.vcs_protocol.create_pull_request(title, description, source_branch, target_branch)

    def _prepare_new_version(self, track: str, source_branch, target_branch) -> BaseResponse:
        revision_version = self.vcs_protocol.get_ci_variables("REVISION_VERSION")
        build_version = self.vcs_protocol.get_ci_variables("BUILD_NUMBER")
        if track == 'production':
            logs_title = "DEVELOPMENT_TICKETS"
            title = f"MR for {track} v3.1.{revision_version}.{build_version}"
        else:
            logs_title = "RELEASE_TICKETS"
            title = f"MR for {track} v3.1.{revision_version}"

        logs = self.vcs_protocol.get_ci_variables(logs_title)
        message = self.issue_tracker.get_beautified_logs(logs)

        response = self.vcs_protocol.create_pull_request(title, message, source_branch, target_branch)
        if response.status_code == requests.codes.created:
            return response
        else:
            match = re.search(r'!(\d+)', response.message)

            if match:
                merge_request_number = match.group(1)
                return self.vcs_protocol.get_pull_request_details(merge_request_number)
            else:
                return response
