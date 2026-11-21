from typing import List, Dict, Any
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_projects_keyboard(draft_key: int, projects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = []
    row = []

    for p in projects:
        name = p.get("name", "Project")
        icon = p.get("icon") or "📁"
        btn_text = f"{icon} {name}"
        if len(btn_text) > 28:
            btn_text = btn_text[:25] + "…"
        row.append(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"lin:{draft_key}:{p['id']}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="📥 General Inbox (No Project)",
                callback_data=f"lin:{draft_key}:none",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data=f"lin:{draft_key}:cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
