from typing import Protocol

from rest_framework.response import Response


class VcsResponseModel:
    def __init__(self, source_branch, target_branch, iid, url_link, title, description, merge_status, draft,
                 should_delete_source):
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.iid = iid
        self.url_link = url_link
        self.title = title
        self.description = description
        self.merge_status = merge_status
        self.draft = draft
        self.should_delete_source = should_delete_source


def class_to_dict(obj):
    if isinstance(obj, list):
        return [class_to_dict(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return obj.__slots__


class BaseResponse:

    def __init__(self, status_code: int, data=None, message: str = None, response=None):
        self.status_code = status_code
        self.success = status_code < 203
        self.data = data
        self.message = message
        self.response = response

    @staticmethod
    def create_from_response(response, status_code, parse, parse_error):
        if response.status_code == status_code:
            model = parse(response.json())
            return BaseResponse(response.status_code, data=model, response=response)
        else:
            json = response.json()
            error_message = parse_error(json)
            return BaseResponse(response.status_code, message=error_message, response=response)

    def to_drf_response(self, excepted_status: int) -> Response:
        json = class_to_dict(self.data)
        response = {
            'success': self.status_code == excepted_status,
            'data': json,
            'message': self.message
        }
        return Response(status=self.status_code, data=response)


class VcsProtocol(Protocol):
    def get_pull_request_details(self, mr_id) -> BaseResponse:
        pass

    def get_pull_requests(self, state: str = 'opened', source: str = None, target: str = None) -> BaseResponse:
        pass

    def create_pull_request(self, title: str, description: str, source: str, target: str) -> BaseResponse:
        pass

    def merge_pull_request(self, mr_id, **params) -> BaseResponse:
        pass

    def get_ci_variables(self, name: str, **params) -> BaseResponse:
        pass

    def check_branch_exists(self, branch_name: str) -> bool:
        pass

    def edit_pull_request(self, mr_id, title: str = None, description: str = None, source: str = None,
                          target: str = None, remove_source: bool = None) -> BaseResponse:
        pass

    def check_id_mr_mergeable(self, mr_id) -> BaseResponse:
        pass

    def provide_project_access_status(self) -> BaseResponse:
        pass

    def request_project_access(self) -> BaseResponse:
        pass
