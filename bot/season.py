"""
Quarterly season rollover (TZ §3.2).

On the 1st day of each quarter the season ends:
  Promotion  — TOP-3 of each league (meeting the qualification minimum, KM) move up.
  Relegation — bottom-3 of each league (except Novice) move down.
  Reset      — season_xp -> 0 for everyone (global_xp persists).
  Notify     — league changes are pushed to users via the bot.

Idempotent: the processed quarter is stored in app_config.last_season, so the
rollover runs exactly once per quarter even though the checker ticks often.
On first run it only records the current quarter (no mid-quarter reset).
"""
import asyncio
from datetime import datetime, timezone
from collections import defaultdict

import asyncpg
from aiogram import Bot
from loguru import logger

from .notifier import _connect

CHECK_INTERVAL = 6 * 3600  # check every 6 hours

LEAGUE_ORDER = ["novice", "amateur", "professional", "innovator"]
LEAGUE_RU = {"novice": "Новичок", "amateur": "Любитель",
             "professional": "Профессионал", "innovator": "Новатор"}
# Qualification minimum (season_xp) required to be promoted FROM a league. Admin-tunable.
KM_PROMOTE = {"novice": 30, "amateur": 100, "professional": 250}


def _current_quarter(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"


async def _run_rollover(conn: asyncpg.Connection) -> int:
    users = await conn.fetch(
        "SELECT id, league, season_xp FROM profiles WHERE role = 'user'"
    )
    by_league = defaultdict(list)
    for u in users:
        by_league[u["league"] or "novice"].append(u)

    moves = {}  # id -> (old_league, new_league)

    # Promotion: TOP-3 per league (excluding the top league), if they meet KM.
    for i, lg in enumerate(LEAGUE_ORDER[:-1]):
        grp = sorted(by_league.get(lg, []), key=lambda u: u["season_xp"] or 0, reverse=True)
        for u in grp[:3]:
            if (u["season_xp"] or 0) >= KM_PROMOTE[lg]:
                moves[u["id"]] = (lg, LEAGUE_ORDER[i + 1])

    # Relegation: bottom-3 per league (excluding Novice), only if the league has
    # enough members to avoid emptying it; never relegate someone just promoted.
    for i, lg in enumerate(LEAGUE_ORDER):
        if i == 0:
            continue
        grp = sorted(by_league.get(lg, []), key=lambda u: u["season_xp"] or 0)  # ascending
        if len(grp) < 4:
            continue
        for u in grp[:3]:
            if u["id"] in moves:
                continue
            moves[u["id"]] = (lg, LEAGUE_ORDER[i - 1])

    # Apply league changes + queue notifications.
    for uid, (old, new) in moves.items():
        await conn.execute("UPDATE profiles SET league = $1 WHERE id = $2", new, uid)
        up = LEAGUE_ORDER.index(new) > LEAGUE_ORDER.index(old)
        title = "🏆 Повышение в лиге!" if up else "📉 Понижение в лиге"
        body = f"Сезон завершён. Ваша лига: {LEAGUE_RU[old]} → {LEAGUE_RU[new]}."
        await conn.execute(
            """INSERT INTO notifications (user_id, type, title, body, is_read, tg_pushed)
               VALUES ($1, 'league_change', $2, $3, false, false)""",
            uid, title, body,
        )

    # Reset season XP for everyone except the admin observer.
    await conn.execute("UPDATE profiles SET season_xp = 0 WHERE role <> 'admin'")
    return len(moves)


async def _tick(conn: asyncpg.Connection) -> None:
    now_q = _current_quarter()
    last = await conn.fetchval("SELECT value FROM app_config WHERE key = 'last_season'")
    if last is None:
        # First run ever — just record the quarter, don't reset mid-season.
        await conn.execute(
            "INSERT INTO app_config (key, value) VALUES ('last_season', $1) "
            "ON CONFLICT (key) DO UPDATE SET value = $1, updated_at = now()", now_q)
        return
    if last == now_q:
        return  # already processed this quarter
    logger.info(f"🏁 Season rollover: {last} -> {now_q}")
    moved = await _run_rollover(conn)
    await conn.execute(
        "UPDATE app_config SET value = $1, updated_at = now() WHERE key = 'last_season'", now_q)
    logger.info(f"[season] rollover complete: {moved} league change(s), season_xp reset")


async def run_season_cron(bot: Bot) -> None:
    logger.info("📅 Season CRON started")
    conn = await _connect()
    while True:
        try:
            await _tick(conn)
        except (asyncpg.PostgresError, ConnectionError, OSError) as e:
            logger.warning(f"[season] DB error, reconnecting: {e}")
            try:
                await conn.close()
            except Exception:  # noqa: BLE001
                pass
            conn = await _connect()
        except Exception as e:  # noqa: BLE001
            logger.error(f"[season] unexpected: {e}")
        await asyncio.sleep(CHECK_INTERVAL)
