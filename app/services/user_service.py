import random
import string
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserPreference
from app.models.game import GameAccount, AccountVerification
from app.models.ratings import PlatformRating
from app.adapters.registry import registry
from app.auth.session import hash_password
from app.utils.logger import logger

def generate_verification_code() -> str:
    """Generate cryptographically random single-use verification code e.g. GB-7F2K"""
    chars = string.ascii_uppercase + string.digits
    rand_part = ''.join(secrets.choice(chars) for _ in range(4))
    return f"GB-{rand_part}"

class UserService:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        username: str,
        display_name: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        city: str = "Addis Ababa",
        language: str = "en",
        role: str = "player",
        telegram_id: Optional[int] = None,
        is_demo: bool = False
    ) -> User:
        # Check uniqueness
        stmt = select(User).where(User.username == username.strip().lower())
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValueError(f"Username '{username}' is already taken.")

        public_id = f"et-{username.strip().lower()}-{secrets.token_hex(2)}"
        pwd_hash = hash_password(password) if password else None

        user = User(
            username=username.strip().lower(),
            display_name=display_name.strip(),
            password_hash=pwd_hash,
            email=email.strip().lower() if email else None,
            city=city,
            role=role,
            telegram_id=telegram_id,
            public_identifier=public_id,
            is_demo=is_demo
        )
        db.add(user)
        await db.flush()

        # User preferences
        pref = UserPreference(
            user_id=user.id,
            language=language
        )
        db.add(pref)

        # Default platform Elo rating record
        rating = PlatformRating(
            user_id=user.id,
            game_key="lichess",
            mode="rapid",
            elo=1200.0,
            matches_played=0,
            tier="Bronze",
            is_demo=is_demo
        )
        db.add(rating)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def request_game_account_link(
        db: AsyncSession,
        user_id: str,
        game_key: str,
        external_username: str,
        is_demo: bool = False
    ) -> Tuple[GameAccount, str]:
        # Validate adapter exists
        adapter = registry.get(game_key)
        if not adapter:
            raise ValueError(f"Game adapter '{game_key}' not supported.")

        clean_external = external_username.strip()

        # Check if external account already linked to another user
        stmt_ext = select(GameAccount).where(
            GameAccount.game_key == game_key,
            GameAccount.external_username == clean_external
        )
        existing_ext = (await db.execute(stmt_ext)).scalar_one_or_none()
        if existing_ext and existing_ext.user_id != user_id:
            raise ValueError(f"External account '{clean_external}' is already linked to another player.")

        # Check if user already linked this game
        stmt_user = select(GameAccount).where(
            GameAccount.user_id == user_id,
            GameAccount.game_key == game_key
        )
        existing_acc = (await db.execute(stmt_user)).scalar_one_or_none()

        code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(hours=2)

        if existing_acc:
            existing_acc.external_username = clean_external
            existing_acc.status = "pending_verification"
            existing_acc.bio_code = code
            existing_acc.bio_code_expires_at = expires_at
            game_account = existing_acc
        else:
            game_account = GameAccount(
                user_id=user_id,
                game_key=game_key,
                external_username=clean_external,
                status="pending_verification",
                bio_code=code,
                bio_code_expires_at=expires_at,
                is_demo=is_demo
            )
            db.add(game_account)

        await db.flush()

        # Add verification attempt record
        verif = AccountVerification(
            game_account_id=game_account.id,
            code=code,
            status="pending"
        )
        db.add(verif)
        await db.commit()
        await db.refresh(game_account)
        return game_account, code

    @staticmethod
    async def verify_game_account(db: AsyncSession, game_account_id: str, user_id: str) -> Tuple[bool, str]:
        stmt = select(GameAccount).where(
            GameAccount.id == game_account_id,
            GameAccount.user_id == user_id
        )
        acc = (await db.execute(stmt)).scalar_one_or_none()
        if not acc:
            return False, "Game account record not found."

        if acc.status == "verified":
            return True, "Account is already verified."

        adapter = registry.get(acc.game_key)
        if not adapter:
            return False, f"Adapter {acc.game_key} not found."

        result = await adapter.verify_owner(acc.external_username, acc.bio_code)
        
        # Record attempt
        verif_stmt = select(AccountVerification).where(
            AccountVerification.game_account_id == acc.id,
            AccountVerification.code == acc.bio_code
        )
        verif = (await db.execute(verif_stmt)).scalar_one_or_none()
        if verif:
            verif.attempts += 1
            verif.checked_at = datetime.utcnow()

        if result.is_verified:
            acc.status = "verified"
            acc.verified_at = datetime.utcnow()
            if verif:
                verif.status = "verified"
            await db.commit()
            return True, "Ownership verified successfully!"
        else:
            if verif:
                verif.error_message = result.error_message
            await db.commit()
            return False, result.error_message or "Verification code not found in external profile."
