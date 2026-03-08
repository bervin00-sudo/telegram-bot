#!/usr/bin/env python3
"""
Userbot — мониторинг всех входящих сообщений аккаунта.
Использует общий Telethon-клиент из telethon_client.py.
"""

import asyncio
import logging
from telethon import events
from telethon.tl.types import User

import ai_assistant
from telethon_client import get_client
from config import validate_userbot_config

logger = logging.getLogger(__name__)

# Минимальная длина текста для автоматического анализа
MIN_TEXT_LENGTH = 10

# Чаты, которые нужно игнорировать (добавь chat_id сюда)
IGNORED_CHATS: set[int] = set()


def _get_sender_name(sender) -> str:
    if isinstance(sender, User):
        parts = [sender.first_name or '', sender.last_name or '']
        name = ' '.join(p for p in parts if p).strip()
        return f"{name} (@{sender.username})" if sender.username else name or f"ID:{sender.id}"
    title = getattr(sender, 'title', None)
    return title or f"ID:{sender.id}"


async def _analyze_and_notify(client, sender_name: str, text: str):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, ai_assistant.analyze_message, text)
        notification = (
            f"📨 **Новое сообщение от {sender_name}:**\n"
            f"```\n{text[:300]}{'...' if len(text) > 300 else ''}\n```\n\n"
            f"🤖 **AI-анализ и варианты ответа:**\n\n{result}"
        )
        await client.send_message('me', notification, parse_mode='markdown')
    except Exception as e:
        logger.error(f"Ошибка при анализе/уведомлении: {e}")


def register_handlers(client):
    """Регистрирует обработчики событий userbot на переданном клиенте."""

    @client.on(events.NewMessage(incoming=True))
    async def handle_incoming(event):
        text = event.message.text or event.message.caption or ''
        if not text or len(text) < MIN_TEXT_LENGTH:
            return
        if event.chat_id in IGNORED_CHATS:
            return

        sender = await event.get_sender()
        if isinstance(sender, User) and sender.bot:
            return

        sender_name = _get_sender_name(sender)
        logger.info(f"Userbot: сообщение от {sender_name}")
        asyncio.create_task(_analyze_and_notify(client, sender_name, text))


async def run_userbot():
    """Запускает userbot как standalone (без run.py)."""
    validate_userbot_config()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    client = get_client()
    register_handlers(client)

    print("Запуск userbot…")
    print("При первом запуске введи номер телефона и код из Telegram.\n")

    async with client:
        me = await client.get_me()
        await client.send_message(
            'me',
            f"✅ Userbot запущен для **{me.first_name}** (@{me.username or me.id})\n"
            f"Все входящие сообщения длиннее {MIN_TEXT_LENGTH} символов будут анализироваться.\n"
            f"AI-ответы приходят сюда, в Избранное.",
            parse_mode='markdown'
        )
        logger.info(f"Userbot запущен для @{me.username or me.id}")
        await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(run_userbot())
