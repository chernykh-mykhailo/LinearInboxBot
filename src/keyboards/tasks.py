from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_tasks_keyboard(
    projects: List[Dict[str, Any]],
    current_filter: Optional[str] = None,  # None means "all"
) -> InlineKeyboardMarkup:
    buttons = []

    # Row 1: All Projects (highlighted if active)
    all_label = "✅ 🌐 Всі проєкти" if not current_filter else "🌐 Всі проєкти"
    buttons.append([InlineKeyboardButton(text=all_label, callback_data="tasks:filter:all")])

    # Dynamic project filter buttons (2 per row)
    row = []
    for p in projects:
        p_id = p.get("id")
        name = p.get("name", "Project")
        icon = p.get("icon") or "📁"
        is_selected = (current_filter == p_id)
        prefix = "✅ " if is_selected else ""
        btn_text = f"{prefix}{icon} {name}"
        if len(btn_text) > 26:
            btn_text = btn_text[:23] + "…"

        row.append(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"tasks:filter:{p_id}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Action row: Refresh
    refresh_key = current_filter if current_filter else "all"
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Оновити список",
                callback_data=f"tasks:refresh:{refresh_key}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
