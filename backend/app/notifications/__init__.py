"""Notification plugins - Telegram, Email, etc."""

from app.notifications.telegram import TelegramNotifier

__all__ = [
    "TelegramNotifier",
]
