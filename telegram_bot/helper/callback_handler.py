from abc import ABC, abstractmethod

from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from sevices.assistant.base_assistant import BaseAssistant
from sevices.issue_tracker.jira_service import JiraService
from sevices.vcs.gitlab_service import GitlabService
from telegram_bot.helper import django_helper
from telegram_bot.helper.sender import call_async


class BaseHandler(ABC):
    loading_message = None
    user = None
    project_id = None

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context

    @abstractmethod
    def from_user(self):
        pass

    @abstractmethod
    def get_project_id(self):
        pass

    async def initialize(self):
        telegram_user = self.from_user()
        self.user = await django_helper.get_user_by_telegram_user(telegram_user.id)

        self.project_id = self.get_project_id()
        if self.project_id:
            access = await django_helper.get_access(self.user, self.project_id)
            await call_async(self._create_services, access)
        return self

    async def show_loading(self):
        self.loading_message = await self.context.bot.send_message(chat_id=self.update.effective_chat.id,
                                                                   text='Подождите идет обработка '
                                                                        'на стороне сервера...')

    async def hide_loading(self):
        if self.loading_message:
            await self.loading_message.delete()
            self.loading_message = None

    async def send_bot_message(self, message: str, reply_markup: InlineKeyboardMarkup = None):
        await self.context.bot.send_message(chat_id=self.update.effective_chat.id, text=message,
                                            parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
                                            reply_markup=reply_markup)

    def _create_services(self, access):
        vcs = GitlabService(access.project, access)
        issue_tracker = JiraService(access.project, access)
        self.assistant = BaseAssistant(vcs, issue_tracker)


class MyCommandHandler(BaseHandler):

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        super().__init__(update, context)
        self.params = {}
        for arg in context.args:
            key, value = arg.split('=')
            self.params[key] = value
        if 'project_id' in self.params:
            self.context.chat_data['project_id'] = self.params['project_id']

    def from_user(self):
        return self.update.message.from_user

    def get_project_id(self):
        if 'project_id' in self.params:
            return self.params['project_id']
        else:
            return None


class MyCallbackQueryHandler(BaseHandler):

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        super().__init__(update, context)
        self.params = {}
        data = update.callback_query.data.split(' ')
        for arg in data[1:]:
            key, value = arg.split('=')
            self.params[key] = value
        if 'project_id' in self.params:
            self.context.chat_data['project_id'] = self.params['project_id']

    async def send_bot_message(self, message: str, reply_markup: InlineKeyboardMarkup = None):
        await self.update.callback_query.answer()
        await self.update.callback_query.message.delete()
        await super().send_bot_message(message, reply_markup)

    def from_user(self):
        return self.update.callback_query.from_user

    def get_project_id(self):
        if 'project_id' in self.params:
            return self.params['project_id']
        else:
            return None


class MyCommonHandler(BaseHandler):
    telegram_user = None

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        super().__init__(update, context)
        self.params = {}
        if hasattr(update, 'callback_query'):
            self.telegram_user = update.callback_query.from_user
            data = update.callback_query.data.split(' ')
            for arg in data[1:]:
                key, value = arg.split('=')
                self.params[key] = value
        elif hasattr(update, 'message'):
            self.telegram_user = update.message.from_user
            for arg in context.args:
                key, value = arg.split('=')
                self.params[key] = value
        if 'project_id' in self.params:
            self.context.chat_data['project_id'] = self.params['project_id']

    def from_user(self):
        return self.telegram_user

    def get_project_id(self):
        if 'project_id' in self.params:
            return self.params['project_id']
        else:
            return None


class MyConversationHandler(BaseHandler):

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        super().__init__(update, context)
        data = update.message.text
        self.data = data

    def get_project_id(self):
        if 'project_id' in self.context.chat_data:
            return self.context.chat_data['project_id']

    def from_user(self):
        return self.update.message.from_user

    def save(self, key, value):
        self.context.chat_data[key] = value

    def get(self, key):
        return self.context.chat_data[key]
