import html
import logging
from typing import Any, Dict, List, Optional
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from src.config import is_authorized
from src.linear_client import LinearClient
from src.keyboards.tasks import build_tasks_keyboard

logger = logging.getLogger(__name__)
router = Router(name="tasks")

STATE_ICONS = {
    "backlog": "📦",
    "unstarted": "⏳",
    "started": "🟡",
    "completed": "✅",
    "canceled": "❌",
}

PRIORITY_BADGES = {
    1: "🔴 P0",
    2: "🟠 P1",
    3: "🟡 P2",
    4: "🔵 P3",
}


def _format_issues_list(
    issues: List[Dict[str, Any]],
    project_name: Optional[str] = None,
) -> str:
    header = (
        f"📁 <b>Задачі: {html.escape(project_name)}</b>"
        if project_name
        else "🌐 <b>Всі активні задачі в Linear</b>"
    )

    if not issues:
        return f"{header}\n\n<i>Задач не знайдено (список порожній).</i>"

    lines = [f"{header} <i>({len(issues)})</i>\n"]

    for issue in issues:
        identifier = issue.get("identifier", "TASK")
        title = html.escape(issue.get("title", "No Title"))
        url = issue.get("url", "https://linear.app")
        state_obj = issue.get("state") or {}
        state_name = state_obj.get("name", "Unknown")
        state_type = state_obj.get("type", "backlog")
        state_icon = STATE_ICONS.get(state_type, "▫️")

        proj = issue.get("project")
        proj_name = f" • <i>{html.escape(proj.get('name'))}</i>" if proj else ""

        priority = issue.get("priority", 0)
        p_badge = f" • <b>{PRIORITY_BADGES[priority]}</b>" if priority in PRIORITY_BADGES else ""

        lines.append(
            f"{state_icon} <a href='{url}'><b>[{identifier}]</b></a> {title}\n"
            f"   └ <i>{html.escape(state_name)}</i>{proj_name}{p_badge}"
        )

    return "\n".join(lines)


def register_tasks_router(linear: LinearClient) -> Router:
    @router.message(Command("tasks"))
    async def cmd_tasks(message: types.Message):
        if not is_authorized(message.from_user.id):
            return

        status_msg = await message.answer("⏳ <i>Завантажую задачі з Linear...</i>")
        try:
            issues = await linear.get_issues(project_id=None, limit=12)
            projects = linear.get_projects()
            text = _format_issues_list(issues, project_name=None)
            keyboard = build_tasks_keyboard(projects, current_filter=None)
            await status_msg.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as e:
            logger.exception("Failed to load issues:")
            await status_msg.edit_text(f"❌ <b>Помилка завантаження:</b> <code>{html.escape(str(e))}</code>")

    @router.callback_query(F.data.startswith("tasks:filter:"))
    async def cb_filter_tasks(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        choice = query.data.split(":", 2)[2]
        project_id = None if choice == "all" else choice

        project_name = None
        projects = linear.get_projects()
        if project_id:
            for p in projects:
                if p["id"] == project_id:
                    project_name = p.get("name")
                    break

        try:
            await query.answer("Завантаження...")
            issues = await linear.get_issues(project_id=project_id, limit=12)
            text = _format_issues_list(issues, project_name=project_name)
            keyboard = build_tasks_keyboard(projects, current_filter=project_id)
            await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as e:
            logger.exception("Failed to filter issues:")
            await query.answer(f"Помилка: {e}", show_alert=True)

    @router.callback_query(F.data.startswith("tasks:refresh:"))
    async def cb_refresh_tasks(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        choice = query.data.split(":", 2)[2]
        project_id = None if choice == "all" else choice

        try:
            await linear.refresh_workspace_data()
            projects = linear.get_projects()
            project_name = None
            if project_id:
                for p in projects:
                    if p["id"] == project_id:
                        project_name = p.get("name")
                        break

            issues = await linear.get_issues(project_id=project_id, limit=12)
            text = _format_issues_list(issues, project_name=project_name)
            keyboard = build_tasks_keyboard(projects, current_filter=project_id)
            await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
            await query.answer("🔄 Список оновлено!")
        except Exception as e:
            logger.exception("Failed to refresh issues:")
            await query.answer(f"Помилка: {e}", show_alert=True)

    return router
