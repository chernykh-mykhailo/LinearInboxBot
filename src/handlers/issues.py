import logging
from typing import Dict, Any
from aiogram import Router, F, types
from aiogram.types import CallbackQuery

from src.config import is_authorized
from src.linear_client import LinearClient
from src.keyboards.projects import build_projects_keyboard

logger = logging.getLogger(__name__)
router = Router(name="issues")

pending_drafts: Dict[int, Dict[str, Any]] = {}


def register_issues_router(linear: LinearClient) -> Router:
    @router.message(F.text | F.photo | F.caption)
    async def handle_incoming_idea(message: types.Message):
        if not is_authorized(message.from_user.id):
            return

        raw_text = message.text or message.caption or ""
        if not raw_text.strip():
            await message.answer("⚠️ Send some text or a photo caption describing the issue.")
            return

        lines = raw_text.strip().split("\n", 1)
        title = lines[0].strip()
        if len(title) > 100:
            title = title[:97] + "…"

        description = lines[1].strip() if len(lines) > 1 else ""

        if message.photo:
            description = (
                f"{description}\n\n<i>[Attached photo/screenshot sent in Telegram]</i>".strip()
            )

        draft_key = message.message_id
        pending_drafts[draft_key] = {
            "title": title,
            "description": description,
            "user_id": message.from_user.id,
        }

        projects = linear.get_projects()
        keyboard = build_projects_keyboard(draft_key, projects)

        preview_text = f"<b>{title}</b>"
        if description:
            preview_text += f"\n<i>{description[:120]}...</i>" if len(description) > 120 else f"\n<i>{description}</i>"

        await message.reply(
            f"📝 <b>Where should this issue be created in Linear?</b>\n\n"
            f"{preview_text}",
            reply_markup=keyboard,
        )

    @router.callback_query(F.data.startswith("lin:"))
    async def handle_project_selection(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        parts = query.data.split(":")
        if len(parts) != 3:
            await query.answer()
            return

        _, draft_key_str, project_choice = parts
        draft_key = int(draft_key_str)

        draft = pending_drafts.get(draft_key)
        if not draft:
            await query.message.edit_text("⌛ This action has expired. Please send the task again.")
            return

        if project_choice == "cancel":
            pending_drafts.pop(draft_key, None)
            await query.message.edit_text("❌ Action cancelled.")
            return

        project_id = None if project_choice == "none" else project_choice
        project_name = "General Inbox"

        if project_id:
            for p in linear.get_projects():
                if p["id"] == project_id:
                    project_name = p.get("name", "Project")
                    break

        await query.message.edit_text(f"⏳ Creating task in <b>{project_name}</b>...")

        try:
            issue = await linear.create_issue(
                title=draft["title"],
                description=draft["description"] or None,
                project_id=project_id,
            )
            pending_drafts.pop(draft_key, None)

            identifier = issue.get("identifier", "TASK")
            issue_title = issue.get("title", draft["title"])
            issue_url = issue.get("url", "https://linear.app")

            await query.message.edit_text(
                f"✅ <b>Issue successfully created!</b>\n\n"
                f"📋 <b>[{identifier}]</b> {issue_title}\n"
                f"📁 <b>Project:</b> {project_name}\n\n"
                f"🔗 <a href='{issue_url}'>Open in Linear ↗</a>",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.exception("Failed to create issue in Linear:")
            await query.message.edit_text(
                f"❌ <b>Error creating Linear issue:</b>\n"
                f"<code>{str(e)}</code>\n\n"
                f"<i>Try /reload or check your API key.</i>"
            )

    return router
