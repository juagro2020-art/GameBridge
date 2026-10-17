from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.token import TokenValidationError
from app.config import settings
from app.bots.handlers import router
from app.utils.logger import logger

# Format-compliant dummy token (46 chars: 10 digits + ':' + 35 chars)
DEFAULT_DEV_TOKEN = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"

def create_bot() -> tuple[Optional[Bot], Dispatcher]:
    dp = Dispatcher()
    dp.include_router(router)
    token = settings.TELEGRAM_BOT_TOKEN or DEFAULT_DEV_TOKEN
    try:
        bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    except TokenValidationError:
        logger.warning("Configured TELEGRAM_BOT_TOKEN failed format validation. Using development fallback bot.")
        bot = Bot(
            token=DEFAULT_DEV_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    return bot, dp

bot, dp = create_bot()
