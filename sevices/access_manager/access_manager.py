from typing import Protocol

from sevices.vcs.vcs_protocol import BaseResponse


class AccessManager(Protocol):

    def provide_vcs_access_status(self) -> BaseResponse:
        pass

    def request_vcs_access(self) -> BaseResponse:
        pass