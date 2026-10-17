import hmac
import hashlib
import urllib.parse
import json
import time
from typing import Optional, Dict, Any
from app.config import settings
from app.utils.logger import logger

def validate_telegram_init_data(init_data: str, bot_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Validates Telegram WebApp initData string using the official algorithm:
    1. Parse query string into key-value pairs.
    2. Extract 'hash' parameter.
    3. Sort remaining keys lexicographically and join with '\n'.
    4. secret_key = HMAC-SHA256(key="WebAppData", msg=bot_token).
    5. calculated_hash = HMAC-SHA256(key=secret_key, msg=data_check_string).
    6. Verify calculated_hash == hash and auth_date freshness.
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    if not init_data or not token:
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Build data-check-string
        items = sorted([f"{k}={v}" for k, v in parsed_data.items()])
        data_check_string = "\n".join(items)

        # secret_key = HMAC-SHA256("WebAppData", bot_token)
        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("Telegram initData hash mismatch")
            return None

        # Check auth_date (e.g. within 24 hours to prevent replay)
        auth_date = int(parsed_data.get("auth_date", 0))
        current_time = int(time.time())
        if current_time - auth_date > 86400:  # 24h expiration
            logger.warning("Telegram initData expired")
            return None

        # Extract user object
        user_raw = parsed_data.get("user")
        if user_raw:
            user_data = json.loads(user_raw)
            return user_data

        return parsed_data
    except Exception as e:
        logger.error(f"Error validating Telegram initData: {e}")
        return None
