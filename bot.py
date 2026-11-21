import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from linear_client import LinearClient

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("LinearInboxBot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")

if not BOT_TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN in .env!")
    sys.exit(1)

if not LINEAR_API_KEY:
    logger.error("Missing LINEAR_API_KEY in .env!")
    sys.exit(1)

ALLOWED_USER_IDS = [
    int(uid.strip()) for uid in ALLOWED_USER_IDS_RAW.split(",") if uid.strip().isdigit()
]

linear = LinearClient(LINEAR_API_KEY)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Memory store for pending tasks: message_id -> draft data
pending_drafts: Dict[int, Dict[str, Any]] = {}


def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


def build_projects_keyboard(draft_key: int) -> InlineKeyboardMarkup:
    projects = linear.get_projects()
    buttons = []

    # Two buttons per row for projects
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

    # Inbox & Cancel options
    buttons.append(
        [
            InlineKeyboardButton(
                text="📥 Тільки Inbox (без проєкту)",
                callback_data=f"lin:{draft_key}:none",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data=f"lin:{draft_key}:cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if not is_authorized(message.from_user.id):
        await message.answer("⛔ Доступ обмежено.")
        return

    projects = linear.get_projects()
    teams = linear.get_teams()

    team_names = ", ".join(t.get("name", "") for t in teams) or "Не знайдено"

    await message.answer(
        f"⚡ <b>MyshCode Linear Inbox Bot активний!</b>\n\n"
        f"🏢 <b>Команди:</b> {team_names}\n"
        f"📁 <b>Активні проєкти ({len(projects)}):</b>\n"
        + "\n".join(f"• {p.get('name')}" for p in projects[:10])
        + (f"\n<i>...та ще {len(projects) - 10}</i>" if len(projects) > 10 else "")
        + "\n\n💡 <i>Просто напиши мені будь-яку ідею чи задачу (або надішли фото), і я закину її в Linear!</i>"
    )


@dp.message(Command("reload"))
async def cmd_reload(message: types.Message):
    if not is_authorized(message.from_user.id):
        return

    try:
        await linear.refresh_workspace_data()
        projects = linear.get_projects()
        await message.answer(
            f"🔄 <b>Дані Linear оновлено!</b>\n"
            f"Знайдено проєктів: <b>{len(projects)}</b>"
        )
    except Exception as e:
        logger.exception("Failed to reload Linear workspace:")
        await message.answer(f"❌ Помилка оновлення: <code>{e}</code>")


@dp.message(F.text | F.photo | F.caption)
async def handle_incoming_idea(message: types.Message):
    if not is_authorized(message.from_user.id):
        return

    raw_text = message.text or message.caption or ""
    if not raw_text.strip():
        await message.answer("⚠️ Надішліть текст або підпис до фото з описом ідеї.")
        return

    # Split title and description
    lines = raw_text.strip().split("\n", 1)
    title = lines[0].strip()
    # Cap title to 100 characters if too long
    if len(title) > 100:
        title = title[:97] + "…"

    description = lines[1].strip() if len(lines) > 1 else ""

    # If photo attached, note it in description
    if message.photo:
        description = (
            f"{description}\n\n<i>[До таски в Telegram було додано скріншот/фото]</i>".strip()
        )

    draft_key = message.message_id
    pending_drafts[draft_key] = {
        "title": title,
        "description": description,
        "user_id": message.from_user.id,
    }

    keyboard = build_projects_keyboard(draft_key)

    preview_text = f"<b>{title}</b>"
    if description:
        preview_text += f"\n<i>{description[:120]}...</i>" if len(description) > 120 else f"\n<i>{description}</i>"

    await message.reply(
        f"📝 <b>Куди записати ідею в Linear?</b>\n\n"
        f"{preview_text}",
        reply_markup=keyboard,
    )


@dp.callback_query(F.data.startswith("lin:"))
async def handle_project_selection(query: CallbackQuery):
    if not is_authorized(query.from_user.id):
        await query.answer("⛔ Немає доступу.", show_alert=True)
        return

    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer()
        return

    _, draft_key_str, project_choice = parts
    draft_key = int(draft_key_str)

    draft = pending_drafts.get(draft_key)
    if not draft:
        await query.message.edit_text("⌛ Ця дія застаріла. Надішліть ідею ще раз.")
        return

    if project_choice == "cancel":
        pending_drafts.pop(draft_key, None)
        await query.message.edit_text("❌ Запис скасовано.")
        return

    project_id = None if project_choice == "none" else project_choice
    project_name = "Загальний Inbox"

    if project_id:
        for p in linear.get_projects():
            if p["id"] == project_id:
                project_name = p.get("name", "Проєкт")
                break

    await query.message.edit_text(f"⏳ Створюю задачу в <b>{project_name}</b>...")

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
            f"✅ <b>Задачу успішно створено!</b>\n\n"
            f"📋 <b>[{identifier}]</b> {issue_title}\n"
            f"📁 <b>Проєкт:</b> {project_name}\n\n"
            f"🔗 <a href='{issue_url}'>Відкрити в Linear ↗</a>",
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.exception("Failed to create issue in Linear:")
        await query.message.edit_text(
            f"❌ <b>Помилка створення в Linear:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"<i>Спробуйте команду /reload або перевірте API-ключ.</i>"
        )


async def main():
    logger.info("Initializing Linear client...")
    try:
        await linear.refresh_workspace_data()
    except Exception as e:
        logger.warning(
            f"Could not connect to Linear at startup: {e}. Bot will still run, use /reload later."
        )

    logger.info("Starting Telegram Bot Polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
