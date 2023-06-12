import os

import django
import telegram

from sevices.vcs.vcs_protocol import BaseResponse
from telegram_bot.helper.sender import call_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArielProject.settings')

django.setup()
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler

from telegram_bot.helper.callback_handler import MyCommandHandler, MyCallbackQueryHandler, MyCommonHandler, \
    MyConversationHandler
from telegram_bot.helper.response_parse_helper import parse_projects, parse_mr_details, parse_mr_list_as_message
from telegram_bot.helper.django_helper import get_project_from_user

from telegram_bot.helper import django_helper


class RegistrationFlow:

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        username = user.username

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Hi, {username}. \nPlease login with data, provided by your admin"
                                            f"\nExample /login username password")

    @staticmethod
    async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_user = update.message.from_user
        args = context.args
        if len(args) == 2:
            username, password = args[0], args[1]

            get_user_sync = sync_to_async(django_helper.get_user)
            user = await get_user_sync(username, password)
            if user:
                user.last_name = f"{telegram_user.id}"
                save_user_async = sync_to_async(user.save)
                await save_user_async()
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Аккаунт {user.first_name} успешно зарегестрирвоан")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Пользователь не найден")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Incorrect number of arguments.")

    def register(self, application):
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('login', self.login))


class ProjectAssistantFlow:

    @staticmethod
    async def projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyCommandHandler(update, context).initialize()
        await handler.show_loading()
        projects = await get_project_from_user(handler.user)
        message = parse_projects(projects)
        keyboard = []

        for item in projects:
            id = item['pk']
            name = item['name']
            keyboard.append([InlineKeyboardButton(name, callback_data=f'action_project project_id={id}')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await handler.hide_loading()
        await handler.send_bot_message(message, reply_markup)

    @staticmethod
    async def action_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyCallbackQueryHandler(update, context).initialize()
        await handler.show_loading()
        id = handler.project_id
        keyboard = [
            [InlineKeyboardButton('Создать мерж реквест', callback_data=f'create_mr project_id={id}')],
            [InlineKeyboardButton('Список мерж реквестов', callback_data=f'mrs project_id={handler.project_id}')],
            [InlineKeyboardButton('Подготовка альфа релиза', callback_data=f'alpha project_id={handler.project_id}')],
            [InlineKeyboardButton('Подготовка бета релиза', callback_data=f'beta project_id={handler.project_id}')],
            [InlineKeyboardButton('Подготовка прод релиза', callback_data=f'prod project_id={handler.project_id}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await handler.hide_loading()
        await handler.send_bot_message('Что собираемся сделать?', reply_markup)

    def register(self, application):
        application.add_handler(CommandHandler('projects', self.projects))
        application.add_handler(CallbackQueryHandler(self.action_project, pattern=r'^action_project project_id=\d+$'))


class CreatePullRequest:
    START, ASK_TITLE, ASK_MESSAGE, ASK_BRANCHES, CONFIRM = range(5)

    async def create_pull_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyCommonHandler(update, context).initialize()
        await handler.send_bot_message('Какие ветки необходимо смерджить? Отправтье в виде:\n '
                                       'source_branch&target_branch')
        return self.ASK_BRANCHES

    async def receive_branches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyConversationHandler(update, context).initialize()
        answer = handler.data.split('&')
        if len(answer) != 2:
            await handler.send_bot_message('Ошибка шаблона сообщения')
            return ConversationHandler.END
        if await call_async(handler.assistant.check_branch_exists, answer[0]):
            source = answer[0]
        else:
            source = None
        if await call_async(handler.assistant.check_branch_exists, answer[1]):
            target = answer[1]
        else:
            target = None

        if source and target:
            handler.save('source', source)
            handler.save('target', target)
            await handler.send_bot_message(f'Какой заголовок указать?.\nЧтобы взять заголовок с Jira, введите fit')
            return self.ASK_TITLE
        elif not source:
            await handler.send_bot_message(f'Ветки {answer[0]} не сущетсвует. Проверьте и переотправьте')
        else:
            await handler.send_bot_message(f'Ветки {answer[1]} не сущетсвует. Проверьте и переотправьте')

    async def receive_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyConversationHandler(update, context).initialize()
        if handler.data.lower() == 'fit':
            source_branch = handler.get('source')
            ticket_id = handler.assistant.issue_tracker.get_ticket_id_from_branch(source_branch)
            response = handler.assistant.issue_tracker.get_issue_details(ticket_id)
            if response.success:
                title = response.data.title
                handler.save('title', title)
                await handler.send_bot_message('Введите описание. Используйте плейсхолдер &tojira, '
                                       'чтобы указать в описаниие ссылку на тикет в Jira')
                return self.ASK_MESSAGE
            else:
                await handler.send_bot_message(
                    f'Не удалось получить тикет. Ошибка: {response.message}. Пожалуйста введите заголовок вручную')

        else:
            handler.save('title', handler.data)
            await handler.send_bot_message('Введите описание. Используйте плейсхолдер &tojira, '
                                       'чтобы указать в описаниие ссылку на тикет в Jira')
            return self.ASK_MESSAGE

    async def receive_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyConversationHandler(update, context).initialize()
        answer = handler.data
        if '&tojira' in answer:
            source_branch = handler.get('source')
            ticket_id = handler.assistant.issue_tracker.get_ticket_id_from_branch(source_branch)
            jira_link = await call_async(handler.assistant.issue_tracker.format_link_for_issue_in_vsc_description,
                                         ticket_id)
            answer = answer.replace('&tojira', jira_link)

        handler.save('description', answer)
        source = handler.get('source')
        target = handler.get('target')
        title = handler.get('title')
        await handler.send_bot_message(f'Настройки приняты\nЗапрос на слияние ветки {source} в {target}\n'
                                       f'Заголовок: {title}\n'
                                       f'Описание: {answer}.\n\nВсе верно? Да/Нет')
        return self.CONFIRM

    async def confirm_creation_mr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyConversationHandler(update, context).initialize()
        answer = handler.data
        if answer.lower() == 'да':
            source = handler.get('source')
            target = handler.get('target')
            title = handler.get('title')
            description = handler.get('description')
            response: BaseResponse = await call_async(handler.assistant.create_pull_request, title, description, source, target)
            if response.success:
                message = parse_mr_details(response.response, "Мр успешно создан")
            else:
                message = response.message
            await handler.send_bot_message(message)
        else:
            await handler.send_bot_message('Отмена создания МР')
        return ConversationHandler.END

    def register(self, application):
        create_mr = CallbackQueryHandler(self.create_pull_request, pattern=r'^create_mr project_id=\d+$')
        conversation_handler = ConversationHandler(
            entry_points=[create_mr],
            states={
                self.ASK_TITLE: [MessageHandler(telegram.ext.filters.TEXT, self.receive_title)],
                self.ASK_MESSAGE: [MessageHandler(telegram.ext.filters.TEXT, self.receive_description)],
                self.ASK_BRANCHES: [MessageHandler(telegram.ext.filters.TEXT, self.receive_branches)],
                self.CONFIRM: [MessageHandler(telegram.ext.filters.TEXT, self.confirm_creation_mr)]
            },
            fallbacks=[]
        )
        application.add_handler(conversation_handler)
        application.add_handler(create_mr)


class GetPullRequests:

    @staticmethod
    async def get_pull_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = await MyCallbackQueryHandler(update, context).initialize()
        response = await call_async(handler.assistant.get_pull_requests)
        message = parse_mr_list_as_message(response.response, 'Пустой список доступных МР')
        await handler.send_bot_message(message)

    def register(self, application):
        create_mr = CallbackQueryHandler(self.get_pull_requests, pattern=r'^mrs project_id=\d+$')
        application.add_handler(create_mr)
