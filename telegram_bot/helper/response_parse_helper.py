import requests

from sevices.vcs.vcs_protocol import BaseResponse


def parse_projects(json) -> str:
    if len(json) == 0:
        return 'У вас нет доступов к проектам. Обратитесь к вашему администратору, чтобы получить доступ'

    message = 'Выберите доступный вам проект из списка:\n'
    for item in json:
        name = item['name']
        message += f' - {name}\n'
    return message


def parse_mr_details(response, success_message: str, jira_link: str = None) -> str:
    if response.status_code < requests.codes.accepted:
        if isinstance(response.json(), list):
            json = response.json()[0]
        else:
            json = response.json()
        source = json['source_branch'].replace('_', '\_')
        target = json['target_branch'].replace('_', '\_')
        iid = json['iid']
        web_url = json['web_url']
        title = json['title'].replace('_', '\_')
        description = json['description'].replace('_', '\_')
        status = json['detailed_merge_status'].replace('_', ' ')
        message = f'{success_message}\n\n' \
                  f'Запрос на слияние {source} в {target}\n' \
                  f'Идентификатор: {iid}\n' \
                  f'Статус: {status}\n' \
                  f'Заголовок: {title}\nОписание:\n{description}\n\n' \
                  f'Ссылка на [gitlab]({web_url})'
        if jira_link:
            message += f'\n[Ссылка на Jira]({jira_link})'
        return message
    else:
        json = response.json()
        error_message = json.get('message', json.get('error', 'Unexpected error on external service occurred'))
        if isinstance(error_message, list):
            developer_error_message = error_message[0]
        else:
            developer_error_message = error_message
        return developer_error_message


def parse_mr_list_as_message(response: BaseResponse, empty_message='Список пуст') -> str:
    if response.success and isinstance(response.data, list):
        data = response.data
        if len(data) == 0:
            return empty_message
        message = ''
        last = data[-1]
        for item in data:
            source = item.source_branch
            target = item.target_branch
            id = item.iid
            url = item.url_link
            id_link = f'[{id}]({url})'
            title = item.title
            status = item.merge_status
            message += f'_{title}_\n{id_link} - {source} -> {target}\nГотовность слияния: *{status}*'
            if id != last.iid:
                message += '\n\n'
        return message
    else:
        return response.message


def parse_value(response, name: str):
    if response.status_code < requests.codes.accepted:
        if isinstance(response.json(), list):
            json = response.json()[0]
        else:
            json = response.json()
        return json[name]
    else:
        json = response.json()
        error_message = json.get('message', json.get('error', 'Unexpected error on external service occurred'))
        if isinstance(error_message, list):
            developer_error_message = error_message[0]
        else:
            developer_error_message = error_message
        return developer_error_message
