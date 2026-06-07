from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from ..keyboards import main_webapp_button, expert_webapp_button
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import settings

router = Router()


def _welcome_text(name: str) -> str:
    hi = f"👋 Assalomu alaykum, <b>{name}</b>!" if name else "👋 Assalomu alaykum!"
    return f"""{hi}

🏥 <b>Tibbiyot Novatorlari</b>
<i>Sog'liqni saqlash innovatsiyalari platformasi</i>

Bu yerda siz:
💡 Innovatsion g'oyangizni yuborasiz
🔬 3 ta ekspert uni anonim baholaydi <i>(Blind Review)</i>
🏆 XP yig'ib, 4 liga bo'ylab yuqoriga ko'tarilasiz
🤝 Mentor va Inkubatordan foydalanasiz

━━━━━━━━━━━━━━━

🇷🇺 <b>Платформа медицинских инноваций</b>
💡 Подайте идею → 🔬 оценка 3 экспертов → 🏆 рост по лигам и кадровый резерв Минздрава

⬇️ <b>Boshlash uchun tugmani bosing / Нажмите кнопку ниже</b>"""


EXPERT_WELCOME_TEXT = """🔬 <b>Tibbiyot Novatorlari — Ekspert kabineti</b>

Xush kelibsiz! Loyihalar teglaringiz bo'yicha avtomatik tushadi.

📋 Har bir loyihani ko'rib chiqing
✅ Tasdiqlash · ↩️ Qayta ishlash · ✗ Rad etish
✍️ Har bir qaror — kamida 150 so'zlik retsenziya
🏅 Har bir retsenziya uchun <b>+20 XP</b>
⏰ SLA: 7 kun

━━━━━━━━━━━━━━━

🇷🇺 <b>Экспертный кабинет.</b> Проекты приходят автоматически по вашим тегам. Решение — с рецензией ≥150 слов. За рецензию +20 XP, срок 7 дней."""


@router.message(CommandStart())
async def cmd_start(message: Message):
    name = (message.from_user.first_name or "").strip()
    if message.from_user.id in settings.expert_ids_set:
        await message.answer(EXPERT_WELCOME_TEXT, reply_markup=expert_webapp_button())
    else:
        await message.answer(
            _welcome_text(name),
            reply_markup=main_webapp_button("🚀 Platformani ochish / Открыть платформу"),
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = """ℹ️ <b>Yordam / Помощь</b>

<b>Buyruqlar / Команды:</b>
🚀 /start — Platformani ochish / Открыть платформу
👤 /profile — Profil, XP va liga / Профиль, XP и лига
📁 /projects — Loyihalarim / Мои проекты
ℹ️ /help — Yordam / Помощь

❓ Savollar bo'lsa / По вопросам: @support_tibbiyot"""
    await message.answer(text, reply_markup=main_webapp_button())


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    await message.answer(
        "👤 <b>Profilingiz / Ваш профиль</b>\n\n"
        "XP, liga, streak va yutuqlaringizni ilovada ko'ring.\n"
        "<i>Откройте приложение, чтобы увидеть XP, лигу и достижения.</i>",
        reply_markup=main_webapp_button("👤 Profilni ochish / Открыть профиль"),
    )


@router.message(Command("projects"))
async def cmd_projects(message: Message):
    await message.answer(
        "📁 <b>Loyihalaringiz / Ваши проекты</b>\n\n"
        "Yuborgan loyihalaringiz holatini kuzating.\n"
        "<i>Следите за статусом поданных проектов в приложении.</i>",
        reply_markup=main_webapp_button("📁 Loyihalarim / Мои проекты"),
    )
