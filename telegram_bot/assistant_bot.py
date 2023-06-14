import logging
from telegram.ext import ApplicationBuilder

from telegram_bot.flows import RegistrationFlow, ProjectAssistantFlow, CreatePullRequest, GetPullRequests, \
    PrepareRelease

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    application = ApplicationBuilder().token('6100934569:AAHwnDP97Cho7h3nDdD_gvzWLaIrw8TsBmA').build()

    RegistrationFlow().register(application)
    ProjectAssistantFlow().register(application)
    CreatePullRequest().register(application)
    GetPullRequests().register(application)
    PrepareRelease().register(application)

    application.run_polling()
