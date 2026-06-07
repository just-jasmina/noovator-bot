"""
SLA watcher (TZ §3.1).

Each review has a 7-day SLA. When an expert lets it lapse without a decision,
the project is automatically re-routed to a *reserve* expert (matching tags, not
already on the project, lowest load) with a fresh 3-day SLA. The reserve expert
gets an in-app notification.

Runs hourly inside the bot process.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import asyncpg
from aiogram import Bot
from loguru import logger

from .notifier import _connect

SLA_INTERVAL = 3600          # check hourly
RESERVE_SLA_DAYS = 3


async def _reassign_overdue(conn: asyncpg.Connection) -> int:
    overdue = await conn.fetch(
        """
        SELECT r.id, r.project_id, r.expert_id, pr.tags
        FROM reviews r
        JOIN projects pr ON pr.id = r.project_id
        WHERE r.decision IS NULL
          AND r.sla_deadline IS NOT NULL
          AND r.sla_deadline < now()
          AND pr.status = 'under_review'
        LIMIT 50
        """
    )
    reassigned = 0
    new_deadline = datetime.now(timezone.utc) + timedelta(days=RESERVE_SLA_DAYS)
    for r in overdue:
        reserve = await conn.fetchrow(
            """
            SELECT p.id
            FROM profiles p
            WHERE p.role = 'expert' AND p.status = 'active'
              AND p.expert_tags && $1::text[]
              AND NOT EXISTS (
                  SELECT 1 FROM reviews r2 WHERE r2.project_id = $2 AND r2.expert_id = p.id
              )
            ORDER BY (SELECT count(*) FROM reviews r3
                      WHERE r3.expert_id = p.id AND r3.reviewed_at IS NULL) ASC
            LIMIT 1
            """,
            r["tags"], r["project_id"],
        )
        if not reserve:
            continue  # no spare expert — leave the original assignment in place
        # Swap the lapsed reviewer for the reserve one.
        await conn.execute("DELETE FROM reviews WHERE id = $1", r["id"])
        await conn.execute(
            "INSERT INTO reviews (project_id, expert_id, sla_deadline) VALUES ($1, $2, $3)",
            r["project_id"], reserve["id"], new_deadline,
        )
        await conn.execute(
            """
            INSERT INTO notifications (user_id, type, title, body, project_id, is_read, tg_pushed)
            VALUES ($1, 'review_assigned', $2, $3, $4, false, false)
            """,
            reserve["id"],
            "📋 Yangi loyiha (zaxira ekspert)",
            "SLA muddati o'tgani uchun loyiha sizga qayta tayinlandi. Muddat: 3 kun.",
            r["project_id"],
        )
        reassigned += 1
    return reassigned


async def run_sla_watch(bot: Bot) -> None:
    logger.info("⏰ SLA watcher started")
    conn = await _connect()
    while True:
        try:
            n = await _reassign_overdue(conn)
            if n:
                logger.info(f"[sla] reassigned {n} overdue review(s) to reserve experts")
        except (asyncpg.PostgresError, ConnectionError, OSError) as e:
            logger.warning(f"[sla] DB error, reconnecting: {e}")
            try:
                await conn.close()
            except Exception:  # noqa: BLE001
                pass
            conn = await _connect()
        except Exception as e:  # noqa: BLE001
            logger.error(f"[sla] unexpected: {e}")
        await asyncio.sleep(SLA_INTERVAL)
