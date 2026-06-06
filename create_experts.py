"""
Generate 40 expert accounts and insert them into the database.
Run: python create_experts.py

Outputs:
  - experts_credentials.csv  — distribute to experts
  - experts_credentials.txt  — human-readable list
"""

import asyncio
import csv
import random
import string
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from backend.database import async_session, create_tables
from backend.models.user import User, UserRole, UserStatus, UserLeague
from backend.services.auth import hash_password


# 40 experts distributed across 12 tags (3-4 per tag)
EXPERTS = [
    # Organizatsiya_sog'liqni_saqlash — 4
    {"username": "org_expert_1", "tag": "Organizatsiya_sog'liqni_saqlash", "display": "Sog'liqni saqlash tashkilotchisi 1"},
    {"username": "org_expert_2", "tag": "Organizatsiya_sog'liqni_saqlash", "display": "Sog'liqni saqlash tashkilotchisi 2"},
    {"username": "org_expert_3", "tag": "Organizatsiya_sog'liqni_saqlash", "display": "Sog'liqni saqlash tashkilotchisi 3"},
    {"username": "org_expert_4", "tag": "Organizatsiya_sog'liqni_saqlash", "display": "Sog'liqni saqlash tashkilotchisi 4"},

    # IT_va_Raqamlashtirish — 4
    {"username": "it_expert_1",  "tag": "IT_va_Raqamlashtirish", "display": "IT va Raqamlashtirish eksperti 1"},
    {"username": "it_expert_2",  "tag": "IT_va_Raqamlashtirish", "display": "IT va Raqamlashtirish eksperti 2"},
    {"username": "it_expert_3",  "tag": "IT_va_Raqamlashtirish", "display": "IT va Raqamlashtirish eksperti 3"},
    {"username": "it_expert_4",  "tag": "IT_va_Raqamlashtirish", "display": "IT va Raqamlashtirish eksperti 4"},

    # Moliya_va_Iqtisodiyot — 3
    {"username": "mol_expert_1", "tag": "Moliya_va_Iqtisodiyot", "display": "Moliya va Iqtisodiyot eksperti 1"},
    {"username": "mol_expert_2", "tag": "Moliya_va_Iqtisodiyot", "display": "Moliya va Iqtisodiyot eksperti 2"},
    {"username": "mol_expert_3", "tag": "Moliya_va_Iqtisodiyot", "display": "Moliya va Iqtisodiyot eksperti 3"},

    # Jarrohlik_amaliyoti — 3
    {"username": "jar_expert_1", "tag": "Jarrohlik_amaliyoti", "display": "Jarrohlik amaliyoti eksperti 1"},
    {"username": "jar_expert_2", "tag": "Jarrohlik_amaliyoti", "display": "Jarrohlik amaliyoti eksperti 2"},
    {"username": "jar_expert_3", "tag": "Jarrohlik_amaliyoti", "display": "Jarrohlik amaliyoti eksperti 3"},

    # Med_huquq — 3
    {"username": "mhq_expert_1", "tag": "Med_huquq", "display": "Tibbiyot huquqi eksperti 1"},
    {"username": "mhq_expert_2", "tag": "Med_huquq", "display": "Tibbiyot huquqi eksperti 2"},
    {"username": "mhq_expert_3", "tag": "Med_huquq", "display": "Tibbiyot huquqi eksperti 3"},

    # Farmakologiya — 3
    {"username": "far_expert_1", "tag": "Farmakologiya", "display": "Farmakologiya eksperti 1"},
    {"username": "far_expert_2", "tag": "Farmakologiya", "display": "Farmakologiya eksperti 2"},
    {"username": "far_expert_3", "tag": "Farmakologiya", "display": "Farmakologiya eksperti 3"},

    # Pediatriya — 3
    {"username": "ped_expert_1", "tag": "Pediatriya", "display": "Pediatriya eksperti 1"},
    {"username": "ped_expert_2", "tag": "Pediatriya", "display": "Pediatriya eksperti 2"},
    {"username": "ped_expert_3", "tag": "Pediatriya", "display": "Pediatriya eksperti 3"},

    # Medtexnika — 4
    {"username": "mtx_expert_1", "tag": "Medtexnika", "display": "Medtexnika eksperti 1"},
    {"username": "mtx_expert_2", "tag": "Medtexnika", "display": "Medtexnika eksperti 2"},
    {"username": "mtx_expert_3", "tag": "Medtexnika", "display": "Medtexnika eksperti 3"},
    {"username": "mtx_expert_4", "tag": "Medtexnika", "display": "Medtexnika eksperti 4"},

    # Sun'iy_intellekt — 4
    {"username": "ai_expert_1",  "tag": "Sun'iy_intellekt", "display": "Sun'iy intellekt eksperti 1"},
    {"username": "ai_expert_2",  "tag": "Sun'iy_intellekt", "display": "Sun'iy intellekt eksperti 2"},
    {"username": "ai_expert_3",  "tag": "Sun'iy_intellekt", "display": "Sun'iy intellekt eksperti 3"},
    {"username": "ai_expert_4",  "tag": "Sun'iy_intellekt", "display": "Sun'iy intellekt eksperti 4"},

    # Sanitariya_Epidemiologiya — 3
    {"username": "san_expert_1", "tag": "Sanitariya_Epidemiologiya", "display": "Sanitariya Epidemiologiya eksperti 1"},
    {"username": "san_expert_2", "tag": "Sanitariya_Epidemiologiya", "display": "Sanitariya Epidemiologiya eksperti 2"},
    {"username": "san_expert_3", "tag": "Sanitariya_Epidemiologiya", "display": "Sanitariya Epidemiologiya eksperti 3"},

    # Tibbiyot_ta'limi — 3
    {"username": "tal_expert_1", "tag": "Tibbiyot_ta'limi", "display": "Tibbiyot ta'limi eksperti 1"},
    {"username": "tal_expert_2", "tag": "Tibbiyot_ta'limi", "display": "Tibbiyot ta'limi eksperti 2"},
    {"username": "tal_expert_3", "tag": "Tibbiyot_ta'limi", "display": "Tibbiyot ta'limi eksperti 3"},

    # Laborator_diagnostika — 3
    {"username": "lab_expert_1", "tag": "Laborator_diagnostika", "display": "Laborator diagnostika eksperti 1"},
    {"username": "lab_expert_2", "tag": "Laborator_diagnostika", "display": "Laborator diagnostika eksperti 2"},
    {"username": "lab_expert_3", "tag": "Laborator_diagnostika", "display": "Laborator diagnostika eksperti 3"},
]


def gen_password(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    # Ensure at least one digit and one letter
    pwd = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
    ]
    pwd += [random.choice(chars) for _ in range(length - 3)]
    random.shuffle(pwd)
    return "".join(pwd)


async def main():
    await create_tables()

    results = []

    async with async_session() as session:
        for expert in EXPERTS:
            # Check if already exists
            existing = await session.execute(
                select(User).where(User.expert_username == expert["username"])
            )
            if existing.scalar_one_or_none():
                print(f"[SKIP] {expert['username']} already exists")
                continue

            password = gen_password()
            user = User(
                telegram_id=None,
                role=UserRole.EXPERT,
                status=UserStatus.ACTIVE,
                league=UserLeague.NOVICE,
                first_name=expert["display"],
                expert_username=expert["username"],
                expert_password_hash=hash_password(password),
                expert_tags=expert["tag"],
                language="uz",
            )
            session.add(user)
            await session.flush()
            results.append({
                "username": expert["username"],
                "password": password,
                "tag": expert["tag"],
                "display_name": expert["display"],
                "user_id": user.id,
            })
            print(f"[OK] Created: {expert['username']}  pass={password}  tag={expert['tag']}")

        await session.commit()

    # Write CSV
    csv_path = os.path.join(os.path.dirname(__file__), "experts_credentials.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "password", "tag", "display_name", "user_id"])
        writer.writeheader()
        writer.writerows(results)

    # Write readable TXT
    txt_path = os.path.join(os.path.dirname(__file__), "experts_credentials.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("TIBBIYOT NOVATORLARI — EXPERT CREDENTIALS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Login URL: https://novaator.netlify.app/expert/login\n")
        f.write("=" * 60 + "\n\n")

        current_tag = None
        for r in results:
            if r["tag"] != current_tag:
                current_tag = r["tag"]
                f.write(f"\n[{current_tag}]\n")
                f.write("-" * 40 + "\n")
            f.write(f"  Login:  {r['username']}\n")
            f.write(f"  Parol:  {r['password']}\n\n")

    print(f"\nDone! {len(results)} experts created.")
    print(f"  CSV:  {csv_path}")
    print(f"  TXT:  {txt_path}")


if __name__ == "__main__":
    asyncio.run(main())
