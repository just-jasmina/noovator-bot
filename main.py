"""
Tibbiyot Novatorlari — MVP v1.0
Telegram Mini App for the Ministry of Health, Republic of Uzbekistan

Run:
  python main.py           # starts both backend API + bot
  python main.py --api     # API only
  python main.py --bot     # bot only
"""

import asyncio
import sys
import os
import uvicorn
from loguru import logger


async def run_api():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(
        "backend.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot():
    from bot.bot import run_bot as _run_bot
    await _run_bot()


async def run_all():
    logger.info("🚀 Starting Tibbiyot Novatorlari — API + Bot")
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if arg == "--api":
        asyncio.run(run_api())
    elif arg == "--bot":
        asyncio.run(run_bot())
    else:
        asyncio.run(run_all())
