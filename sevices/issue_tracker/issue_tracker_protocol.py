from typing import Protocol

from sevices.vcs.vcs_protocol import VcsProtocol, BaseResponse


class IssueTrackerProtocol(Protocol):

    def get_issue_details(self, ticket_id) -> BaseResponse:
        pass

    def get_url_for_ticket(self, ticket_id) -> str:
        pass

    def get_ticket_id_from_branch(self, name: str) -> str:
        pass

    def format_title_for_vcs(self, ticket_id) -> str:
        pass

    def format_link_for_issue_in_vsc_description(self, ticket_id, vcs: VcsProtocol, title:str):
        pass

    def get_beautified_logs(self, logs) -> str:
        pass


class IssueTrackerModel:
    def __init__(self, title):
        self.title = title
