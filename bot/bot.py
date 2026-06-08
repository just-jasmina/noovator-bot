import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo
from .handlers import start
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Platformani ochish / Открыть платформу"),
        BotCommand(command="help", description="ℹ️ Yordam / Помощь"),
        BotCommand(command="profile", description="👤 Mening profilim / Мой профиль"),
        BotCommand(command="projects", description="📁 Loyihalarim / Мои проекты"),
    ]
    await bot.set_my_commands(commands)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🏥 Platforma",
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    )


async def run_bot():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start.router)

    await set_bot_commands(bot)

    # Run Telegram polling + background workers (push, SLA watcher, season CRON) together.
    from .notifier import run_notifier
    from .sla import run_sla_watch
    from .season import run_season_cron
    await asyncio.gather(
        dp.start_polling(bot, allowed_updates=["message", "callback_query"]),
        run_notifier(bot),
        run_sla_watch(bot),
        run_season_cron(bot),
    )


if __name__ == "__main__":
    asyncio.run(run_bot())
