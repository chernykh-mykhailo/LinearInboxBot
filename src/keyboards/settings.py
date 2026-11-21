from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_settings_keyboard(ai_enabled: bool, language: str = "uk") -> InlineKeyboardMarkup:
    ai_status = "🟢 Увімкнено" if ai_enabled else "⚪ Вимкнено"
    if language == "en":
        ai_status = "🟢 Enabled" if ai_enabled else "⚪ Disabled"
        ai_label = f"🤖 AI Enhancement: {ai_status}"
        lang_label = "🌐 Language: 🇬🇧 English"
        close_label = "❌ Close"
    else:
        ai_label = f"🤖 ШІ структурування: {ai_status}"
        lang_label = "🌐 Мова: 🇺🇦 Українська"
        close_label = "❌ Закрити"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ai_label, callback_data="set:ai:toggle")],
            [InlineKeyboardButton(text=lang_label, callback_data="set:lang:toggle")],
            [InlineKeyboardButton(text=close_label, callback_data="set:close")],
        ]
    )
