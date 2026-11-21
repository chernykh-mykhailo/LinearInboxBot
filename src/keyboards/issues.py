from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_ai_approval_keyboard(draft_key: int, language: str = "uk") -> InlineKeyboardMarkup:
    if language == "en":
        btn_save = "📁 Choose Project & Save"
        btn_regen = "🔄 Regenerate"
        btn_raw = "📝 Save as Raw"
        btn_cancel = "❌ Cancel"
    else:
        btn_save = "📁 Вибрати проєкт і зберегти"
        btn_regen = "🔄 Перегенерувати"
        btn_raw = "📝 Як сирий текст"
        btn_cancel = "❌ Скасувати"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_save, callback_data=f"act:{draft_key}:choose_project")],
            [
                InlineKeyboardButton(text=btn_regen, callback_data=f"act:{draft_key}:regen"),
                InlineKeyboardButton(text=btn_raw, callback_data=f"act:{draft_key}:raw"),
            ],
            [InlineKeyboardButton(text=btn_cancel, callback_data=f"act:{draft_key}:cancel")],
        ]
    )
