import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from src.config import BOT_TOKEN, LINEAR_API_KEY
from src.linear_client import LinearClient
from src.handlers.commands import register_commands_router
from src.handlers.settings import register_settings_router
from src.handlers.tasks import register_tasks_router
from src.handlers.issues import register_issues_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("LinearInboxBot")


async def main():
    logger.info("Initializing Linear client...")
    linear = LinearClient(LINEAR_API_KEY)

    try:
        await linear.refresh_workspace_data()
    except Exception as e:
        logger.warning(
            f"Could not connect to Linear at startup: {e}. Bot will still run, use /reload later."
        )

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Register modular routers
    dp.include_router(register_commands_router(linear))
    dp.include_router(register_settings_router())
    dp.include_router(register_tasks_router(linear))
    dp.include_router(register_issues_router(linear))

    # Register bot commands menu in Telegram UI
    await bot.set_my_commands(
        [
            BotCommand(command="tasks", description="📋 Активні задачі та фільтри"),
            BotCommand(command="settings", description="⚙️ Налаштування ШІ та мови"),
            BotCommand(command="reload", description="🔄 Оновити проєкти Linear"),
            BotCommand(command="start", description="⚡ Головне меню та статус"),
        ],
        scope=BotCommandScopeDefault(),
    )

    logger.info("Starting Telegram Bot Polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
