import requests

from project.models import Access, Project
from sevices.vcs.vcs_protocol import VcsProtocol, BaseResponse, VcsResponseModel


class GitlabService(VcsProtocol):

    def __init__(self, project: Project, access: Access):
        self.project = project
        self.access = access

    def get_pull_requests(self, state: str = 'opened', source: str = None, target: str = None) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}

        params = {
            'state': state,
            'source_branch': source,
            'target_branch': target
        }

        response = requests.get(url, headers=headers, params=params)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_mr_details,
                                                 self._parse_error)

    def get_pull_request_details(self, mr_id) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests/{mr_id}"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        response = requests.get(url, headers=headers)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_mr_detail,
                                                 self._parse_error)

    def create_pull_request(self, title: str, description: str, source: str, target: str) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        payload = {
            'source_branch': source,
            'target_branch': target,
            'title': title,
            'description': description
        }
        response = requests.post(url, headers=headers, data=payload)
        return BaseResponse.create_from_response(response, requests.codes.created, self._parse_mr_detail,
                                                 self._parse_error)

    def merge_pull_request(self, mr_id, **params) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests/{mr_id}/mergee"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        payload = {
            'merge_when_pipeline_succeeds': False,
        }
        response = requests.put(url, headers=headers, data=payload)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_mr_detail,
                                                 self._parse_error)

    def check_branch_exists(self, branch_name: str) -> bool:
        url = f"{self.project.vcs_base_link}/repository/branches/{branch_name.replace('/', '%2F')}"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True  # Ветка существует
        elif response.status_code == 404:
            return False  # Ветка не существует
        else:
            return False

    def edit_pull_request(self, mr_id, title: str = None, description: str = None, source: str = None,
                          target: str = None, remove_source: bool = None) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests/{mr_id}"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        payload = {
            'title': title,
            'description': description,
            'source_branch': source,
            'target_branch': target,
            'remove_source_branch': remove_source
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        response = requests.put(url, headers=headers, data=payload)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_mr_detail,
                                                 self._parse_error)

    def check_id_mr_mergeable(self, mr_id) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/merge_requests/{mr_id}/merge_status"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        response = requests.get(url, headers=headers)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_mr_mergeable_status,
                                                 self._parse_error)

    def get_ci_variables(self, name: str, **params) -> BaseResponse:
        url = f"{self.project.vcs_base_link}/variables/{name}"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}
        response = requests.get(url, headers=headers, params=params)
        return BaseResponse.create_from_response(response, requests.codes.ok, self._parse_ci_variables,
                                                 self._parse_error)

    def provide_project_access_status(self) -> BaseResponse:
        email = self.access.user.email
        url = f"{self.project.vcs_base_link}/members/all"
        headers = {'Authorization': f'Bearer {self.access.git_token}'}

        url = "https://gitlab.com/api/v4/users"
        params = {"search": email}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]  # Return the first user found

        return BaseResponse(404, message="Не удалось получить информацию о доступе в гитлабе")

    @staticmethod
    def _parse_ci_variables(json):
        variables = json.get('value')
        return variables

    @staticmethod
    def _parse_mr_detail(json) -> VcsResponseModel:
        source = json['source_branch'].replace('_', '\_')
        target = json['target_branch'].replace('_', '\_')
        iid = json['iid']
        web_url = json['web_url']
        title = json['title'].replace('_', '\_')
        description = json['description'].replace('_', '\_')
        status = json['detailed_merge_status'].replace('_', ' ')
        remove_source_branch = json['force_remove_source_branch']

        return VcsResponseModel(source, target, iid, web_url, title, description, status,
                                title.lower().startswith("draft:"), remove_source_branch)

    @staticmethod
    def _parse_mr_mergeable_status(json):
        mergeable_status = json.get('mergeable_status')
        return mergeable_status

    def _parse_mr_details(self, json):
        collection = []

        for item in json:
            collection.append(self._parse_mr_detail(item))

        return collection

    @staticmethod
    def _parse_error(json) -> str:
        error_message = json.get('message', json.get('error', 'Unexpected error on external service occurred'))
        if isinstance(error_message, list):
            developer_error_message = error_message[0]
        else:
            developer_error_message = error_message
        return developer_error_message
