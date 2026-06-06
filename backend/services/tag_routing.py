"""
Supabase-native expert routing by project tags.

The DB has THREE historical tag vocabularies:
  - Experts (profiles.expert_tags):  Uzbek, no apostrophe  -> CANONICAL
  - Frontend (older builds):         Uzbek, with apostrophe
  - Legacy seed projects:            Russian

This module normalises any incoming tag to the canonical expert vocabulary so
that array-overlap matching against profiles.expert_tags actually works.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Canonical tag vocabulary == profiles.expert_tags values
CANONICAL_TAGS = [
    "Organizatsiya_sogliqni_saqlash",
    "IT_va_Raqamlashtirish",
    "Moliya_va_Iqtisodiyot",
    "Jarrohlik_amaliyoti",
    "Med_huquq",
    "Farmakologiya",
    "Pediatriya",
    "Medtexnika",
    "Suniy_intellekt",
    "Sanitariya_Epidemiologiya",
    "Tibbiyot_talimi",
    "Laborator_diagnostika",
]

# Human-readable labels (RU) for UI display
TAG_LABELS = {
    "Organizatsiya_sogliqni_saqlash": "Орг. здравоохранения",
    "IT_va_Raqamlashtirish": "IT и Цифровизация",
    "Moliya_va_Iqtisodiyot": "Финансы и Экономика",
    "Jarrohlik_amaliyoti": "Хирургия",
    "Med_huquq": "Мед. право",
    "Farmakologiya": "Фармакология",
    "Pediatriya": "Педиатрия",
    "Medtexnika": "Медтехника",
    "Suniy_intellekt": "ИИ в медицине",
    "Sanitariya_Epidemiologiya": "Сан-эпидемиология",
    "Tibbiyot_talimi": "Мед. образование",
    "Laborator_diagnostika": "Лаб. диагностика",
}

# Any historical / alternate spelling -> canonical
TAG_ALIASES = {
    # apostrophe variants (older frontend)
    "organizatsiya_sog'liqni_saqlash": "Organizatsiya_sogliqni_saqlash",
    "sun'iy_intellekt": "Suniy_intellekt",
    "tibbiyot_ta'limi": "Tibbiyot_talimi",
    # russian legacy seed tags
    "it и цифровизация": "IT_va_Raqamlashtirish",
    "орг. здравоохранения": "Organizatsiya_sogliqni_saqlash",
    "финансы и экономика": "Moliya_va_Iqtisodiyot",
    "хирургия": "Jarrohlik_amaliyoti",
    "мед. право": "Med_huquq",
    "фармакология": "Farmakologiya",
    "педиатрия": "Pediatriya",
    "медтехника": "Medtexnika",
    "ии в медицине": "Suniy_intellekt",
    "сан-эпидемиология": "Sanitariya_Epidemiologiya",
    "эпидемиология": "Sanitariya_Epidemiologiya",
    "мед. образование": "Tibbiyot_talimi",
    "лаборатория": "Laborator_diagnostika",
    "лаб. диагностика": "Laborator_diagnostika",
}

# Fast lookup: lowercased canonical + alias -> canonical
_LOOKUP = {t.lower(): t for t in CANONICAL_TAGS}
_LOOKUP.update(TAG_ALIASES)


def normalize_tag(tag: str) -> str:
    """Map any spelling to its canonical form. Unknown tags pass through trimmed."""
    if not tag:
        return tag
    key = tag.strip().lower()
    if key in _LOOKUP:
        return _LOOKUP[key]
    # also try apostrophe-stripped match
    key2 = key.replace("'", "").replace("`", "").replace("’", "")
    return _LOOKUP.get(key2, tag.strip())


def normalize_tags(tags: list[str]) -> list[str]:
    seen, out = set(), []
    for t in tags or []:
        n = normalize_tag(t)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def tag_label(tag: str) -> str:
    return TAG_LABELS.get(normalize_tag(tag), tag.replace("_", " "))


async def assign_experts_supabase(
    db: AsyncSession,
    project_id: str,
    raw_tags: list[str],
    max_experts: int = 3,
) -> list[dict]:
    """
    Route a project to experts whose expert_tags overlap the project's tags.
    Picks up to `max_experts` by (overlap desc, current load asc).
    Creates review rows (skipping any that already exist). Returns assigned experts.
    """
    tags = normalize_tags(raw_tags)
    if not tags:
        return []

    rows = await db.execute(
        text("""
            SELECT
                p.id,
                p.full_name,
                p.expert_username,
                cardinality(
                    ARRAY(SELECT unnest(p.expert_tags)
                          INTERSECT
                          SELECT unnest(CAST(:tags AS text[])))
                ) AS overlap,
                (SELECT count(*) FROM reviews r
                   WHERE r.expert_id = p.id AND r.reviewed_at IS NULL) AS load
            FROM profiles p
            WHERE p.role = 'expert'
              AND p.status = 'active'
              AND p.expert_tags && CAST(:tags AS text[])
            ORDER BY overlap DESC, load ASC
            LIMIT :lim
        """),
        {"tags": tags, "lim": max_experts},
    )
    experts = [dict(r) for r in rows.mappings().all()]

    assigned = []
    for e in experts:
        # skip if a review already links this expert to this project
        exists = await db.execute(
            text("SELECT 1 FROM reviews WHERE project_id = :pid AND expert_id = :eid LIMIT 1"),
            {"pid": project_id, "eid": e["id"]},
        )
        if exists.first():
            continue
        await db.execute(
            text("INSERT INTO reviews (project_id, expert_id) VALUES (:pid, :eid)"),
            {"pid": project_id, "eid": e["id"]},
        )
        # notify the expert
        try:
            await db.execute(
                text("""
                    INSERT INTO notifications (user_id, type, title, body, project_id)
                    VALUES (:uid, 'review_assigned', :title, :body, :pid)
                """),
                {
                    "uid": e["id"],
                    "title": "Yangi loyiha retsenziya uchun",
                    "body": "Sizning yo'nalishingiz bo'yicha yangi loyiha keldi.",
                    "pid": project_id,
                },
            )
        except Exception:
            pass
        assigned.append(e)

    return assigned


async def compute_and_apply_decision(db: AsyncSession, project_id: str) -> str | None:
    """
    After experts vote, compute the majority decision and update project status.
    Returns the applied status or None if not enough votes yet.
    """
    rows = await db.execute(
        text("""
            SELECT decision FROM reviews
            WHERE project_id = :pid AND reviewed_at IS NOT NULL AND decision IS NOT NULL
        """),
        {"pid": project_id},
    )
    decisions = [r[0] for r in rows.all()]
    if len(decisions) < 2:
        return None

    approve = decisions.count("approve")
    reject = decisions.count("reject")

    new_status = None
    if approve >= 2:
        new_status = "approved"
    elif reject >= 2:
        new_status = "rejected"
    elif len(decisions) >= 3:
        new_status = "revision"

    if new_status:
        await db.execute(
            text("UPDATE projects SET status = :s WHERE id = :pid"),
            {"s": new_status, "pid": project_id},
        )
    return new_status
