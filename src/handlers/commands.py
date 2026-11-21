import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from src.config import is_authorized
from src.linear_client import LinearClient

logger = logging.getLogger(__name__)
router = Router(name="commands")


def register_commands_router(linear: LinearClient) -> Router:
    @router.message(CommandStart())
    async def cmd_start(message: types.Message):
        if not is_authorized(message.from_user.id):
            await message.answer("⛔ Access restricted.")
            return

        projects = linear.get_projects()
        teams = linear.get_teams()
        team_names = ", ".join(t.get("name", "") for t in teams) or "None found"

        await message.answer(
            f"⚡ <b>Linear Inbox Bot Active</b>\n\n"
            f"🏢 <b>Teams:</b> {team_names}\n"
            f"📁 <b>Active Projects ({len(projects)}):</b>\n"
            + "\n".join(f"• {p.get('name')}" for p in projects[:10])
            + (f"\n<i>...and {len(projects) - 10} more</i>" if len(projects) > 10 else "")
            + "\n\n💡 <i>Send any message, task idea, or screenshot to save it to Linear!</i>"
        )

    @router.message(Command("reload"))
    async def cmd_reload(message: types.Message):
        if not is_authorized(message.from_user.id):
            return

        try:
            await linear.refresh_workspace_data()
            projects = linear.get_projects()
            await message.answer(
                f"🔄 <b>Linear workspace refreshed!</b>\n"
                f"Active projects: <b>{len(projects)}</b>"
            )
        except Exception as e:
            logger.exception("Failed to reload Linear workspace:")
            await message.answer(f"❌ Reload error: <code>{e}</code>")

    return router
