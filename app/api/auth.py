from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserPreference
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.user_service import UserService
from app.auth.session import verify_password, create_session_token, consume_magic_login_token
from app.auth.telegram import validate_telegram_init_data
from app.auth.dependencies import get_current_user_optional, get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(
    data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await UserService.register_user(
            db=db,
            username=data.username,
            display_name=data.display_name,
            password=data.password,
            email=data.email,
            city=data.city,
            language=data.language
        )
        token = create_session_token(user.id, user.role)
        response.set_cookie(
            key="gb_session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )
        response.set_cookie(key="gb_lang", value=data.language, max_age=86400 * 30)
        return {"success": True, "user_id": user.id, "public_identifier": user.public_identifier}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.username == data.username.strip().lower())
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid username or account inactive.")

    # In demo mode, if password not set, allow login
    if user.password_hash and data.password:
        if not verify_password(user.password_hash, data.password):
            raise HTTPException(status_code=401, detail="Invalid password.")

    token = create_session_token(user.id, user.role)
    response.set_cookie(
        key="gb_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )
    
    # Check language preference
    p_stmt = select(UserPreference).where(UserPreference.user_id == user.id)
    pref = (await db.execute(p_stmt)).scalar_one_or_none()
    lang = pref.language if pref else "en"
    response.set_cookie(key="gb_lang", value=lang, max_age=86400 * 30)

    return {"success": True, "role": user.role, "public_identifier": user.public_identifier}

@router.post("/telegram-webapp")
async def telegram_webapp_auth(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    body = await request.json()
    init_data = body.get("init_data")
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing Telegram initData")

    validated = validate_telegram_init_data(init_data)
    if not validated:
        raise HTTPException(status_code=401, detail="Invalid or expired Telegram WebApp authentication")

    tg_id = validated.get("id")
    stmt = select(User).where(User.telegram_id == tg_id)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        # Create user for this Telegram account
        username = validated.get("username") or f"tg_{tg_id}"
        first_name = validated.get("first_name", "Gamer")
        user = await UserService.register_user(
            db=db,
            username=username,
            display_name=first_name,
            telegram_id=tg_id,
            language=validated.get("language_code", "en")
        )

    token = create_session_token(user.id, user.role)
    response.set_cookie(
        key="gb_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )
    return {"success": True, "user_id": user.id, "public_identifier": user.public_identifier}

@router.get("/magic")
async def magic_login(token: str, response: Response, db: AsyncSession = Depends(get_db)):
    user_id = consume_magic_login_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired magic login link")

    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session_token = create_session_token(user.id, user.role)
    response.set_cookie(key="gb_session", value=session_token, httponly=True, samesite="lax")
    return {"success": True, "message": "Successfully logged in via magic link", "redirect": "/dashboard"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("gb_session")
    return {"success": True, "message": "Logged out successfully"}

@router.post("/set-language")
async def set_language(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_optional)
):
    body = await request.json()
    lang = body.get("language", "en")
    if lang not in ["en", "am", "om"]:
        lang = "en"

    response.set_cookie("gb_lang", lang, max_age=86400 * 365)
    if user:
        stmt = select(UserPreference).where(UserPreference.user_id == user.id)
        pref = (await db.execute(stmt)).scalar_one_or_none()
        if pref:
            pref.language = lang
            await db.commit()

    return {"success": True, "language": lang}
