import time
import hmac
import hashlib
import json
import urllib.parse
from app.auth.session import (
    hash_password,
    verify_password,
    create_session_token,
    verify_session_token,
    create_magic_login_token,
    consume_magic_login_token
)
from app.auth.telegram import validate_telegram_init_data

def test_password_hashing():
    pwd = "SecretPassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(hashed, pwd) is True
    assert verify_password(hashed, "WrongPassword") is False

def test_session_token():
    token = create_session_token("user-123", "player", expires_in_seconds=3600)
    payload = verify_session_token(token)
    assert payload is not None
    assert payload["uid"] == "user-123"
    assert payload["role"] == "player"

    # Tampered token
    tampered = token[:-4] + "abcd"
    assert verify_session_token(tampered) is None

    # Expired token
    expired_token = create_session_token("user-123", "player", expires_in_seconds=-10)
    assert verify_session_token(expired_token) is None

def test_magic_login_token_single_use():
    token = create_magic_login_token("user-456", ttl_seconds=300)
    # First consumption succeeds
    uid = consume_magic_login_token(token)
    assert uid == "user-456"
    # Second consumption fails (single-use enforced)
    assert consume_magic_login_token(token) is None

def test_telegram_init_data_validation():
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    user_data = {"id": 99998888, "first_name": "Biruk", "username": "biruk_eth"}
    auth_date = str(int(time.time()))

    params = {
        "auth_date": auth_date,
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user_data)
    }

    # Calculate valid hash using official Telegram procedure
    items = sorted([f"{k}={v}" for k, v in params.items()])
    data_check_string = "\n".join(items)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    valid_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    params["hash"] = valid_hash
    init_data_string = urllib.parse.urlencode(params)

    # Valid check
    validated_user = validate_telegram_init_data(init_data_string, bot_token=bot_token)
    assert validated_user is not None
    assert validated_user["id"] == 99998888
    assert validated_user["first_name"] == "Biruk"

    # Tampered check
    tampered_params = params.copy()
    tampered_params["hash"] = "invalidhash123456"
    tampered_string = urllib.parse.urlencode(tampered_params)
    assert validate_telegram_init_data(tampered_string, bot_token=bot_token) is None
