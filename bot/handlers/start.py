from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.types import MenuButtonWebApp, WebAppInfo
from ..keyboards import main_webapp_button, expert_webapp_button
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import settings

router = Router()

WELCOME_TEXT = """
🏥 <b>Tibbiyot Novatorlari</b>

Sog'liqni saqlash sohasidagi innovatsiyalar platformasiga xush kelibsiz!

<b>Platforma imkoniyatlari:</b>
• 💡 Innovatsion g'oyalarni yuborish
• 🔬 Ekspert baholash (Blind Review)
• 🤝 Mentorlik va Inkubator
• 🏆 Reyting va XP tizimi
• 📊 4 ta liga: Yangi boshlovchi → Novator

---

🏥 <b>Тиббиёт Новаторлари</b>

Добро пожаловать на платформу инноваций в здравоохранении!

<b>Возможности:</b>
• 💡 Подача инновационных идей
• 🔬 Экспертная оценка (Blind Review)
• 🤝 Менторство и Инкубатор
• 🏆 Рейтинг и XP-система
• 📊 4 лиги: Новичок → Новатор
"""

EXPERT_WELCOME_TEXT = """
🔬 <b>Tibbiyot Novatorlari — Ekspert kabineti</b>

Siz ekspert sifatida tizimga kirmoqdasiz.

<b>Ekspert vazifalari:</b>
• 📋 Loyihalarni ko'rib chiqish va baholash
• ✅ Tasdiqlaш / ↩ Qayta ishlash / ✗ Rad etish
• 🏅 Har bir retsenziya uchun +20 XP

---

🔬 <b>Тиббиёт Новаторлари — Экспертный кабинет</b>

Вы входите в систему как эксперт.

<b>Ваши задачи:</b>
• 📋 Рецензировать поданные проекты
• ✅ Одобрить / ↩ На доработку / ✗ Отклонить
• 🏅 За каждую рецензию +20 XP
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id in settings.expert_ids_set:
        await message.answer(
            EXPERT_WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=expert_webapp_button(),
        )
    else:
        await message.answer(
            WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=main_webapp_button("🚀 Platformani ochish / Открыть платформу"),
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "ℹ️ <b>Yordam / Помощь</b>\n\n"
        "/start — Platformani qayta ochish\n"
        "/profile — Profilingiz\n"
        "/projects — Loyihalaringiz\n\n"
        "Muammolar uchun: @support_tibbiyot"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_webapp_button())


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    await message.answer(
        "👤 Profilingizni ko'rish uchun ilovani oching:",
        reply_markup=main_webapp_button("👤 Profilni ko'rish"),
    )


@router.message(Command("projects"))
async def cmd_projects(message: Message):
    await message.answer(
        "📁 Loyihalaringizni ko'rish uchun ilovani oching:",
        reply_markup=main_webapp_button("📁 Loyihalarim"),
    )
