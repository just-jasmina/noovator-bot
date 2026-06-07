from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from backend.config import settings


def main_webapp_button(text: str = "🚀 Ilovani ochish") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=text,
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    ]])


def expert_webapp_button(text: str = "🔬 Ekspert ilovasini ochish / Открыть экспертный кабинет") -> InlineKeyboardMarkup:
    url = f"{settings.WEBAPP_URL}?startapp=expert"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    ]])


def open_project_button(project_id: int) -> InlineKeyboardMarkup:
    url = f"{settings.WEBAPP_URL}?startapp=project_{project_id}"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📄 Loyihani ko'rish / Открыть проект",
            web_app=WebAppInfo(url=url),
        )
    ]])


def open_review_button(project_id: int) -> InlineKeyboardMarkup:
    url = f"{settings.WEBAPP_URL}?startapp=review_{project_id}"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📋 Ekspertiza / К рецензии",
            web_app=WebAppInfo(url=url),
        )
    ]])


def notify_keyboard(ntype: str, project_id=None) -> InlineKeyboardMarkup:
    """Pick the right 'open' button for a push notification by its type."""
    if ntype == "review_assigned":
        return expert_webapp_button("📋 Ekspertizaga o'tish / Перейти к экспертизе")
    if project_id:
        url = f"{settings.WEBAPP_URL}?startapp=project_{project_id}"
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📄 Loyihani ochish / Открыть проект", web_app=WebAppInfo(url=url))
        ]])
    return main_webapp_button("🔍 Ilovani ochish / Открыть приложение")
