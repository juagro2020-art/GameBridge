from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, UserPreference
from app.models.ratings import PlatformRating
from app.bots.keyboards import get_main_menu_keyboard, get_language_selection_keyboard
from app.localization.i18n import t
from app.config import settings
from app.utils.logger import logger

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message):
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or "Gamer"
    username = message.from_user.username or f"tg_{telegram_id}"

    user_lang = "en"
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = (await session.execute(stmt)).scalar_one_or_none()

        if not user:
            # Auto-provision or register user via Telegram
            public_id = f"et-tg-{telegram_id}"
            user = User(
                telegram_id=telegram_id,
                username=username.lower(),
                display_name=first_name,
                role="player",
                city="Addis Ababa",
                public_identifier=public_id,
                is_demo=False
            )
            session.add(user)
            await session.flush()

            pref = UserPreference(user_id=user.id, language="en")
            session.add(pref)

            rating = PlatformRating(
                user_id=user.id,
                game_key="lichess",
                mode="rapid",
                elo=1200.0,
                tier="Bronze"
            )
            session.add(rating)
            await session.commit()
        else:
            p_stmt = select(UserPreference).where(UserPreference.user_id == user.id)
            pref = (await session.execute(p_stmt)).scalar_one_or_none()
            if pref:
                user_lang = pref.language

    welcome_text = (
        f"🎮 **Welcome to GameBridge Ethiopia, {first_name}!**\n\n"
        "The grassroots esports ladder for Ethiopian mobile gamers.\n"
        "• Play in daily community cups\n"
        "• Link your official game accounts\n"
        "• Build your verified Gamer Passport\n"
        "• Climb from City to National rankings!"
        if user_lang != "am" else
        f"🎮 **እንኳን ወደ ጌምብሪጅ ኢትዮጵያ በደህና መጡ፣ {first_name}!**\n\n"
        "የኢትዮጵያ ቀዳሚ የኢ-ስፖርት ውድድር እና ደረጃ መድረክ።\n"
        "• በየቀኑ ማህበረሰብ ዋንጫዎች ላይ ይሳተፉ\n"
        "• ይፋዊ የጌም አካውንቶችዎን ያረጋግጡ\n"
        "• የጌመር ፓስፖርትዎን ይገንቡ\n"
        "• ከከተማ ወደ አገር አቀፍ ደረጃ ያድጉ!"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_lang),
        parse_mode="Markdown"
    )

@router.message(Command("leaderboard"))
async def handle_leaderboard(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(PlatformRating, User).join(User, PlatformRating.user_id == User.id)\
            .order_by(PlatformRating.elo.desc()).limit(5)
        top_players = (await session.execute(stmt)).all()

    text = "🏆 **Top Players — GameBridge Ethiopia**\n\n"
    for rank, (r, u) in enumerate(top_players, start=1):
        text += f"{rank}. **{u.display_name}** ({u.city}) — {int(r.elo)} Elo [{r.tier}]\n"

    await message.answer(text, parse_mode="Markdown")

@router.message(Command("profile"))
async def handle_profile(message: Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            await message.answer("Please send /start to register your account.")
            return

        r_stmt = select(PlatformRating).where(PlatformRating.user_id == user.id)
        rating = (await session.execute(r_stmt)).scalars().first()
        elo = int(rating.elo) if rating else 1200
        tier = rating.tier if rating else "Bronze"

    passport_url = f"{settings.APP_URL}/p/{user.public_identifier}"
    text = (
        f"👤 **Gamer Passport: {user.display_name}**\n"
        f"City: {user.city}\n"
        f"Rating: {elo} Elo ({tier})\n"
        f"Public Passport URL: {passport_url}"
    )
    await message.answer(text)

@router.callback_query(F.data == "cmd_language")
async def handle_lang_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 **Select your preferred language / ቋንቋዎን ይምረጡ:**",
        reply_markup=get_language_selection_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_lang(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if user:
            p_stmt = select(UserPreference).where(UserPreference.user_id == user.id)
            pref = (await session.execute(p_stmt)).scalar_one_or_none()
            if pref:
                pref.language = lang
                await session.commit()

    confirm_msg = "Language set to English! 🇬🇧" if lang == "en" else "ቋንቋዎ ወደ አማርኛ ተቀይሯል! 🇪🇹"
    await callback.message.edit_text(
        confirm_msg,
        reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()
