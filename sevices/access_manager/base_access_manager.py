from sevices.access_manager.access_manager import AccessManager
from sevices.issue_tracker.issue_tracker_protocol import IssueTrackerProtocol
from sevices.vcs.vcs_protocol import BaseResponse, VcsProtocol


class BaseAccessManager(AccessManager):

    def __init__(self, vcs_protocol: VcsProtocol, issue_tracker: IssueTrackerProtocol):
        self.vcs_protocol = vcs_protocol
        self.issue_tracker = issue_tracker


    def provide_vcs_access_status(self) -> BaseResponse:
        return self.vcs_protocol.provide_project_access_status()
