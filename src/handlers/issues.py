import html
import io
import logging
from typing import Any, Dict
from aiogram import Bot, Router, F, types
from aiogram.types import CallbackQuery

from src.config import is_authorized
from src.linear_client import LinearClient
from src.services.ai_service import AIService
from src.services.settings_storage import get_user_settings
from src.keyboards.issues import build_ai_approval_keyboard
from src.keyboards.projects import build_projects_keyboard

logger = logging.getLogger(__name__)
router = Router(name="issues")

# In-memory storage for active draft issues
pending_drafts: Dict[int, Dict[str, Any]] = {}

PRIORITY_LABELS_UK = {
    0: "⚪ Без пріоритету",
    1: "🔴 Терміновий (P0)",
    2: "🟠 Високий (P1)",
    3: "🟡 Середній (P2)",
    4: "🔵 Низький (P3)",
}

PRIORITY_LABELS_EN = {
    0: "⚪ None",
    1: "🔴 Urgent (P0)",
    2: "🟠 High (P1)",
    3: "🟡 Medium (P2)",
    4: "🔵 Low (P3)",
}


def _format_preview(draft: Dict[str, Any], language: str = "uk") -> str:
    title = html.escape(draft.get("title", ""))
    desc = html.escape(draft.get("description", ""))
    transcript = draft.get("transcript")
    priority = draft.get("priority", 0)

    p_map = PRIORITY_LABELS_EN if language == "en" else PRIORITY_LABELS_UK
    p_label = p_map.get(priority, p_map[0])

    if language == "en":
        preview = (
            f"✨ <b>AI Enhanced Task Preview</b>\n\n"
            f"📋 <b>{title}</b>\n"
            f"⚡ <b>Priority:</b> {p_label}\n\n"
        )
        if desc:
            preview += f"📝 <b>Description:</b>\n<pre>{desc}</pre>\n\n"
        if transcript and transcript.strip() != title:
            preview += f"🎙 <i>Transcript: \"{html.escape(transcript[:200])}\"</i>\n\n"
        preview += "<i>Choose an action below:</i>"
    else:
        preview = (
            f"✨ <b>Попередній перегляд (ШІ)</b>\n\n"
            f"📋 <b>{title}</b>\n"
            f"⚡ <b>Пріоритет:</b> {p_label}\n\n"
        )
        if desc:
            preview += f"📝 <b>Опис:</b>\n<pre>{desc}</pre>\n\n"
        if transcript and transcript.strip() != title:
            preview += f"🎙 <i>Розшифровка: «{html.escape(transcript[:200])}»</i>\n\n"
        preview += "<i>Оберіть дію нижче:</i>"

    return preview


def register_issues_router(linear: LinearClient) -> Router:
    ai_service = AIService()

    # 1. Voice & Audio messages
    @router.message(F.voice | F.audio)
    async def handle_voice_message(message: types.Message, bot: Bot):
        if not is_authorized(message.from_user.id):
            return

        settings = get_user_settings(message.from_user.id)
        lang = settings.get("language", "uk")

        if not ai_service.is_configured():
            msg = (
                "⚠️ <b>GEMINI_API_KEY is missing!</b> Voice transcription requires a Google Gemini API key in <code>.env</code>."
                if lang == "en"
                else "⚠️ <b>GEMINI_API_KEY не налаштовано!</b> Для транскрипції войсів потрібен ключ Google Gemini в <code>.env</code>."
            )
            await message.reply(msg)
            return

        status_msg = await message.reply(
            "🎙 <i>Transcribing and structuring audio with Gemini...</i>"
            if lang == "en"
            else "🎙 <i>Транскрибую та аналізую голосове повідомлення через Gemini...</i>"
        )

        try:
            file_id = message.voice.file_id if message.voice else message.audio.file_id
            file = await bot.get_file(file_id)
            file_stream = io.BytesIO()
            await bot.download_file(file.file_path, file_stream)
            audio_bytes = file_stream.getvalue()

            mime_type = "audio/ogg" if message.voice else (message.audio.mime_type or "audio/ogg")
            result = await ai_service.transcribe_and_enhance_audio(
                audio_bytes=audio_bytes,
                mime_type=mime_type,
                language=lang,
            )

            draft_key = message.message_id
            pending_drafts[draft_key] = {
                "title": result["title"],
                "description": result["description"],
                "raw_text": result.get("transcript", result["title"]),
                "transcript": result.get("transcript", ""),
                "priority": result.get("priority", 0),
                "user_id": message.from_user.id,
                "is_ai": True,
            }

            keyboard = build_ai_approval_keyboard(draft_key, language=lang)
            preview_text = _format_preview(pending_drafts[draft_key], language=lang)

            await status_msg.edit_text(preview_text, reply_markup=keyboard)

        except Exception as e:
            logger.exception("Failed to process voice message:")
            await status_msg.edit_text(f"❌ Error processing audio: <code>{html.escape(str(e))}</code>")

    # 2. Text & Screenshot messages
    @router.message(F.text | F.photo)
    async def handle_text_or_photo(message: types.Message):
        if not is_authorized(message.from_user.id):
            return

        raw_text = message.text or message.caption or ""
        if not raw_text.strip():
            await message.answer("⚠️ Send some text, voice note, or screenshot with caption.")
            return

        settings = get_user_settings(message.from_user.id)
        ai_enabled = settings.get("ai_enabled", True)
        lang = settings.get("language", "uk")

        # If user has AI enabled and Gemini key is configured -> run enhancement
        if ai_enabled and ai_service.is_configured():
            status_msg = await message.reply(
                "✨ <i>Structuring task via AI...</i>" if lang == "en" else "✨ <i>Форматую задачу через AI...</i>"
            )
            try:
                result = await ai_service.enhance_text_task(raw_text, language=lang)

                desc = result["description"]
                if message.photo:
                    desc = f"{desc}\n\n<i>[Attached screenshot in Telegram]</i>".strip()

                draft_key = message.message_id
                pending_drafts[draft_key] = {
                    "title": result["title"],
                    "description": desc,
                    "raw_text": raw_text,
                    "priority": result.get("priority", 0),
                    "user_id": message.from_user.id,
                    "is_ai": True,
                }

                keyboard = build_ai_approval_keyboard(draft_key, language=lang)
                preview_text = _format_preview(pending_drafts[draft_key], language=lang)
                await status_msg.edit_text(preview_text, reply_markup=keyboard)
                return
            except Exception as e:
                logger.warning(f"AI enhancement failed, falling back to raw: {e}")
                await status_msg.delete()

        # Raw / Direct Mode
        lines = raw_text.strip().split("\n", 1)
        title = lines[0].strip()
        if len(title) > 100:
            title = title[:97] + "…"
        description = lines[1].strip() if len(lines) > 1 else ""

        if message.photo:
            description = f"{description}\n\n<i>[Attached screenshot in Telegram]</i>".strip()

        draft_key = message.message_id
        pending_drafts[draft_key] = {
            "title": title,
            "description": description,
            "raw_text": raw_text,
            "priority": 0,
            "user_id": message.from_user.id,
            "is_ai": False,
        }

        projects = linear.get_projects()
        keyboard = build_projects_keyboard(draft_key, projects)

        preview_text = f"<b>{html.escape(title)}</b>"
        if description:
            snippet = description[:140] + ("..." if len(description) > 140 else "")
            preview_text += f"\n<i>{html.escape(snippet)}</i>"

        prompt = (
            "📁 <b>Where should this issue be created in Linear?</b>"
            if lang == "en"
            else "📁 <b>У який проєкт Linear додати цю задачу?</b>"
        )
        await message.reply(f"{prompt}\n\n{preview_text}", reply_markup=keyboard)

    # 3. Actions Callback (Regenerate, Raw, Project Select, Cancel)
    @router.callback_query(F.data.startswith("act:"))
    async def handle_ai_action(query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        parts = query.data.split(":")
        if len(parts) != 3:
            await query.answer()
            return

        _, draft_key_str, action = parts
        draft_key = int(draft_key_str)
        draft = pending_drafts.get(draft_key)

        if not draft:
            await query.message.edit_text("⌛ This draft has expired. Send a new message.")
            return

        settings = get_user_settings(query.from_user.id)
        lang = settings.get("language", "uk")

        if action == "cancel":
            pending_drafts.pop(draft_key, None)
            await query.message.edit_text("❌ Скасовано." if lang == "uk" else "❌ Cancelled.")
            return

        if action == "raw":
            raw_text = draft.get("raw_text") or draft["title"]
            lines = raw_text.strip().split("\n", 1)
            draft["title"] = lines[0][:100]
            draft["description"] = lines[1] if len(lines) > 1 else ""
            draft["priority"] = 0

            projects = linear.get_projects()
            keyboard = build_projects_keyboard(draft_key, projects)
            prompt = (
                f"📝 <b>Raw Issue:</b> {html.escape(draft['title'])}\n\nChoose target project:"
                if lang == "en"
                else f"📝 <b>Сирий текст:</b> {html.escape(draft['title'])}\n\nОберіть проєкт:"
            )
            await query.message.edit_text(prompt, reply_markup=keyboard)
            return

        if action == "regen":
            await query.answer("🔄 Перегенеровую..." if lang == "uk" else "🔄 Regenerating...")
            raw_text = draft.get("raw_text") or draft["title"]
            result = await ai_service.enhance_text_task(raw_text, language=lang)
            draft["title"] = result["title"]
            draft["description"] = result["description"]
            draft["priority"] = result.get("priority", 0)

            keyboard = build_ai_approval_keyboard(draft_key, language=lang)
            preview_text = _format_preview(draft, language=lang)
            await query.message.edit_text(preview_text, reply_markup=keyboard)
            return

        if action == "choose_project":
            projects = linear.get_projects()
            keyboard = build_projects_keyboard(draft_key, projects)
            prompt = (
                f"📁 <b>Target Project for:</b> {html.escape(draft['title'])}"
                if lang == "en"
                else f"📁 <b>Оберіть проєкт для задачі:</b>\n<b>{html.escape(draft['title'])}</b>"
            )
            await query.message.edit_text(prompt, reply_markup=keyboard)
            return

    # 4. Project Selection & Linear Issue Creation
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
            await query.message.edit_text("⌛ This draft has expired. Please send the task again.")
            return

        if project_choice == "cancel":
            pending_drafts.pop(draft_key, None)
            await query.message.edit_text("❌ Скасовано.")
            return

        project_id = None if project_choice == "none" else project_choice
        project_name = "General Inbox"

        if project_id:
            for p in linear.get_projects():
                if p["id"] == project_id:
                    project_name = p.get("name", "Project")
                    break

        await query.message.edit_text(f"⏳ Створюю задачу в <b>{html.escape(project_name)}</b>...")

        try:
            issue = await linear.create_issue(
                title=draft["title"],
                description=draft.get("description") or None,
                project_id=project_id,
                priority=draft.get("priority", 0),
            )
            pending_drafts.pop(draft_key, None)

            identifier = issue.get("identifier", "TASK")
            issue_title = issue.get("title", draft["title"])
            issue_url = issue.get("url", "https://linear.app")

            await query.message.edit_text(
                f"✅ <b>Задачу успішно створено!</b>\n\n"
                f"📋 <b>[{identifier}]</b> {html.escape(issue_title)}\n"
                f"📁 <b>Проєкт:</b> {html.escape(project_name)}\n\n"
                f"🔗 <a href='{issue_url}'>Відкрити в Linear ↗</a>",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.exception("Failed to create issue in Linear:")
            await query.message.edit_text(
                f"❌ <b>Помилка створення задачі в Linear:</b>\n"
                f"<code>{html.escape(str(e))}</code>\n\n"
                f"<i>Спробуйте /reload або перевірте права API-ключа.</i>"
            )

    return router
