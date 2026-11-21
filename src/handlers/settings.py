import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from src.config import is_authorized, GEMINI_API_KEY
from src.keyboards.settings import build_settings_keyboard
from src.services.settings_storage import (
    get_user_settings,
    toggle_ai,
    toggle_language,
)

logger = logging.getLogger(__name__)
router = Router(name="settings")


def get_settings_text(user_id: int) -> str:
    settings = get_user_settings(user_id)
    ai_on = settings.get("ai_enabled", True)
    lang = settings.get("language", "uk")

    if lang == "en":
        api_warning = (
            "\n⚠️ <i>GEMINI_API_KEY is not set in .env! AI features will be unavailable.</i>"
            if not GEMINI_API_KEY
            else ""
        )
        return (
            f"⚙️ <b>Bot Settings</b>\n\n"
            f"• <b>AI Issue Structuring:</b> {'🟢 Enabled' if ai_on else '⚪ Disabled'}\n"
            f"• <b>Voice & Issue Language:</b> 🇬🇧 English\n"
            f"{api_warning}\n"
            f"<i>Tap buttons below to toggle options:</i>"
        )
    else:
        api_warning = (
            "\n⚠️ <i>GEMINI_API_KEY не вказано в .env! AI функції будуть недоступні.</i>"
            if not GEMINI_API_KEY
            else ""
        )
        return (
            f"⚙️ <b>Налаштування бота</b>\n\n"
            f"• <b>ШІ структурування задач:</b> {'🟢 Увімкнено' if ai_on else '⚪ Вимкнено'}\n"
            f"• <b>Мова відповідей та задач:</b> 🇺🇦 Українська\n"
            f"{api_warning}\n"
            f"<i>Натисніть кнопку нижче для перемикання:</i>"
        )


def register_settings_router() -> Router:
    @router.message(Command("settings"))
    async def cmd_settings(message: types.Message):
        if not is_authorized(message.from_user.id):
            return

        settings = get_user_settings(message.from_user.id)
        text = get_settings_text(message.from_user.id)
        keyboard = build_settings_keyboard(
            ai_enabled=settings.get("ai_enabled", True),
            language=settings.get("language", "uk"),
        )
        await message.answer(text, reply_markup=keyboard)

    @router.callback_query(F.data == "set:ai:toggle")
    async def cb_toggle_ai(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        toggle_ai(query.from_user.id)
        settings = get_user_settings(query.from_user.id)
        text = get_settings_text(query.from_user.id)
        keyboard = build_settings_keyboard(
            ai_enabled=settings.get("ai_enabled", True),
            language=settings.get("language", "uk"),
        )
        await query.message.edit_text(text, reply_markup=keyboard)
        await query.answer()

    @router.callback_query(F.data == "set:lang:toggle")
    async def cb_toggle_lang(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        toggle_language(query.from_user.id)
        settings = get_user_settings(query.from_user.id)
        text = get_settings_text(query.from_user.id)
        keyboard = build_settings_keyboard(
            ai_enabled=settings.get("ai_enabled", True),
            language=settings.get("language", "uk"),
        )
        await query.message.edit_text(text, reply_markup=keyboard)
        await query.answer()

    @router.callback_query(F.data == "set:close")
    async def cb_close_settings(query: CallbackQuery):
        await query.message.delete()
        await query.answer()

    return router
