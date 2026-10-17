from fastapi import APIRouter, Request, Header, HTTPException, status
from aiogram.types import Update
from app.bots.bot import bot, dp
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # Verify Telegram secret token header if configured
    if settings.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Unauthorized telegram webhook attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret token")

    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}")
        return {"ok": False, "error": str(e)}
