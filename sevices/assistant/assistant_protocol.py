from typing import Protocol

from sevices.vcs.vcs_protocol import BaseResponse


class AssistantProtocol(Protocol):

    def get_pull_requests(self, state: str = 'opened', source: str = None, target: str = None) -> BaseResponse:
        pass

    def create_pull_request(self, title: str, description: str, source: str, target: str) -> BaseResponse:
        pass

    def create_developer_pull_request(self, source_branch) -> BaseResponse:
        pass

    def create_prerelease_pull_request(self, source_branch) -> BaseResponse:
        pass

    def prepare_alpha(self) -> BaseResponse:
        pass

    def publish_beta(self) -> BaseResponse:
        pass

    def publish_production(self) -> BaseResponse:
        pass
