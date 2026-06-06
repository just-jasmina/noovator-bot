import httpx
from ..config import settings
from ..models.notification import Notification, NotificationType


async def send_bot_message(telegram_id: int | None, text: str, reply_markup: dict | None = None):
    """Send message via Telegram Bot API."""
    if not settings.BOT_TOKEN or not telegram_id:
        return
    payload = {"chat_id": telegram_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )


def build_open_app_button(text: str = "Ilovani ochish / Открыть приложение") -> dict:
    return {
        "inline_keyboard": [[
            {"text": text, "web_app": {"url": settings.WEBAPP_URL}}
        ]]
    }


NOTIFICATION_TEXTS = {
    NotificationType.VERIFICATION_APPROVED: (
        "✅ <b>Profilingiz tasdiqlandi!</b>\n"
        "Siz endi loyihalar yuborishingiz mumkin. +50 XP berildi.\n\n"
        "✅ <b>Ваш профиль подтверждён!</b>\nМожете подавать проекты. +50 XP начислено."
    ),
    NotificationType.VERIFICATION_REJECTED: (
        "❌ <b>Profilingiz rad etildi.</b>\n"
        "Sabab: {reason}\n\n"
        "❌ <b>Ваш профиль отклонён.</b>\nПричина: {reason}"
    ),
    NotificationType.REVIEW_VERDICT: (
        "📋 <b>Loyihangiz bo'yicha qaror chiqarildi:</b> {verdict}\n\n"
        "📋 <b>По вашему проекту вынесено решение:</b> {verdict}"
    ),
    NotificationType.MENTOR_REQUEST: (
        "🤝 <b>Mentorlik so'rovi!</b>\n"
        "Kimdir sizni mentor sifatida talab qilmoqda.\n\n"
        "🤝 <b>Запрос на менторство!</b>\nКто-то запросил вас в качестве ментора."
    ),
    NotificationType.LEAGUE_PROMOTED: (
        "🏆 <b>Tabriklaymiz! Siz yangi ligaga o'tdingiz: {league}</b>\n\n"
        "🏆 <b>Поздравляем! Вы перешли в лигу: {league}</b>"
    ),
    NotificationType.LEAGUE_RELEGATED: (
        "⚠️ <b>Siz ligadan tushirib yubordingiz: {league}</b>\n"
        "Faolroq bo'ling!\n\n"
        "⚠️ <b>Вы понижены в лигу: {league}</b>\nБудьте активнее!"
    ),
    NotificationType.PROJECT_TO_PILOT: (
        "🚀 <b>Loyihangiz «Pilot» bosqichiga o'tdi!</b> +500 XP\n\n"
        "🚀 <b>Ваш проект переведён в «Пилот»!</b> +500 XP"
    ),
    NotificationType.PROJECT_SCALED: (
        "🌟 <b>Loyihangiz butun O'zbekiston bo'ylab joriy etildi!</b> +1000 XP\n\n"
        "🌟 <b>Ваш проект масштабирован на всю Республику!</b> +1000 XP"
    ),
}


async def notify_user(telegram_id: int, notif_type: NotificationType, **kwargs):
    template = NOTIFICATION_TEXTS.get(notif_type, "")
    text = template.format(**kwargs) if kwargs else template
    await send_bot_message(telegram_id, text, build_open_app_button())
