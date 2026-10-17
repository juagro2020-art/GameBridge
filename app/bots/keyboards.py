from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings

def get_main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    open_app_text = "🚀 Open GameBridge App" if lang != "am" else "🚀 የጌምብሪጅ መተግበሪያን ክፈት"
    lb_text = "🏆 Leaderboards" if lang != "am" else "🏆 የደረጃ ሰንጠረዥ"
    passport_text = "📜 My Passport" if lang != "am" else "📜 ፓስፖርቴ"
    lang_text = "🌐 Switch Language / ቋንቋ ቀይር"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=open_app_text,
                web_app=WebAppInfo(url=settings.APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text=lb_text, callback_data="cmd_leaderboards"),
            InlineKeyboardButton(text=passport_text, callback_data="cmd_passport")
        ],
        [
            InlineKeyboardButton(text=lang_text, callback_data="cmd_language")
        ]
    ])
    return keyboard

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English 🇬🇧", callback_data="set_lang:en"),
            InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="set_lang:am"),
            InlineKeyboardButton(text="Afaan Oromoo 🇪🇹", callback_data="set_lang:om")
        ]
    ])
