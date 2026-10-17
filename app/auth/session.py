import hmac
import hashlib
import base64
import json
import time
import secrets
from typing import Optional, Dict, Any
from app.config import settings

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt, key_hex = stored_hash.split(":", 1)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False

def create_session_token(user_id: str, role: str, expires_in_seconds: int = 86400 * 7) -> str:
    """Create signed, tamper-proof session token."""
    payload = {
        "uid": user_id,
        "role": role,
        "exp": int(time.time()) + expires_in_seconds
    }
    raw = json.dumps(payload).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw).decode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    if not token or "." not in token:
        return None
    try:
        b64_payload, sig = token.split(".", 1)
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        raw = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

# In-memory single-use magic login tokens store with TTL
_magic_tokens: Dict[str, Dict[str, Any]] = {}

def create_magic_login_token(user_id: str, ttl_seconds: int = 300) -> str:
    token = secrets.token_urlsafe(32)
    _magic_tokens[token] = {
        "user_id": user_id,
        "expires_at": time.time() + ttl_seconds
    }
    return token

def consume_magic_login_token(token: str) -> Optional[str]:
    data = _magic_tokens.pop(token, None)
    if not data:
        return None
    if time.time() > data["expires_at"]:
        return None
    return data["user_id"]
