"""
Push-notification delivery (TZ §7.1).

The Mini App writes rows into the Supabase `notifications` table. This background
task polls that table and delivers every unsent notification to the user's
Telegram chat (looked up via profiles.telegram_id), then marks it `tg_pushed`.

Users without a telegram_id (e.g. web-only experts) are simply skipped — they
see notifications inside the app.
"""
import asyncio
import asyncpg
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from loguru import logger

from backend.config import settings
from .keyboards import notify_keyboard

POLL_INTERVAL = 8  # seconds

# A friendly emoji per notification type (falls back to 🔔).
TYPE_EMOJI = {
    "review_assigned": "📋",
    "approved": "✅",
    "rejected": "📢",
    "revision": "↩️",
    "comment_reply": "💬",
    "mentor_request": "🤝",
    "mentor_assigned": "🤝",
    "incubator_message": "💬",
    "league_change": "🏆",
    "sla": "⏰",
    "profile_verified": "🎉",
}


def _dsn() -> str:
    """asyncpg needs a plain postgresql:// DSN (no +asyncpg/+psycopg2 driver tag)."""
    dsn = settings.SYNC_DATABASE_URL or settings.DATABASE_URL or ""
    return dsn.replace("+asyncpg", "").replace("+psycopg2", "")


async def _connect() -> asyncpg.Connection:
    while True:
        try:
            return await asyncpg.connect(_dsn())
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[notifier] DB connect failed, retrying in 10s: {e}")
            await asyncio.sleep(10)


async def _deliver(bot: Bot, conn: asyncpg.Connection) -> int:
    rows = await conn.fetch(
        """
        SELECT n.id, n.type, n.title, n.body, n.project_id, p.telegram_id
        FROM notifications n
        JOIN profiles p ON p.id = n.user_id
        WHERE n.tg_pushed = false
          AND p.telegram_id IS NOT NULL
        ORDER BY n.created_at ASC
        LIMIT 25
        """
    )
    sent = 0
    for r in rows:
        emoji = TYPE_EMOJI.get(r["type"], "🔔")
        title = (r["title"] or "Bildirishnoma / Уведомление").strip()
        body = (r["body"] or "").strip()
        text = f"{emoji} <b>{title}</b>"
        if body:
            text += f"\n\n{body}"
        try:
            await bot.send_message(
                chat_id=r["telegram_id"],
                text=text,
                parse_mode="HTML",
                reply_markup=notify_keyboard(r["type"], r["project_id"]),
                disable_web_page_preview=True,
            )
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            # User blocked the bot / chat not found — permanent, don't retry.
            logger.info(f"[notifier] skip {r['telegram_id']} ({r['type']}): {e}")
        except Exception as e:  # noqa: BLE001 — transient; still mark to avoid loops
            logger.warning(f"[notifier] send error {r['telegram_id']}: {e}")
        # Mark handled regardless so a single bad row never blocks the queue.
        await conn.execute("UPDATE notifications SET tg_pushed = true WHERE id = $1", r["id"])
    return sent


async def run_notifier(bot: Bot) -> None:
    logger.info("🔔 Notification pusher started")
    conn = await _connect()
    while True:
        try:
            n = await _deliver(bot, conn)
            if n:
                logger.info(f"[notifier] delivered {n} notification(s)")
        except (asyncpg.PostgresError, ConnectionError, OSError) as e:
            logger.warning(f"[notifier] DB error, reconnecting: {e}")
            try:
                await conn.close()
            except Exception:  # noqa: BLE001
                pass
            conn = await _connect()
        except Exception as e:  # noqa: BLE001
            logger.error(f"[notifier] unexpected: {e}")
        await asyncio.sleep(POLL_INTERVAL)
