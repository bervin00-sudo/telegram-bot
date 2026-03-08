#!/usr/bin/env python3
"""
Userbot — доступ ко всем сообщениям аккаунта Telegram.

Использует Telegram MTProto API (Telethon) для чтения всех входящих
сообщений и отправляет AI-анализ с вариантами ответа в "Избранное".

Требует: API_ID и API_HASH из https://my.telegram.org/apps
"""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel, PeerUser

import ai_assistant
from config import API_ID, API_HASH, validate_userbot_config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Имя файла сессии (сохраняет авторизацию между запусками)
SESSION_NAME = 'userbot_session'

# Минимальная длина текста для автоматического анализа (символов)
MIN_TEXT_LENGTH = 10

# Чаты, которые нужно игнорировать (боты, каналы без диалога и т.д.)
IGNORED_CHATS = set()


def format_sender_name(sender) -> str:
    """Возвращает имя отправителя."""
    if isinstance(sender, User):
        parts = [sender.first_name or '', sender.last_name or '']
        name = ' '.join(p for p in parts if p).strip()
        if sender.username:
            return f"{name} (@{sender.username})"
        return name or f"ID:{sender.id}"
    if isinstance(sender, (Chat, Channel)):
        return sender.title or f"Чат ID:{sender.id}"
    return "Неизвестный"


async def analyze_and_notify(client: TelegramClient, event, sender_name: str, text: str):
    """Запускает AI-анализ и отправляет результат в Избранное."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, ai_assistant.analyze_message, text)

        notification = (
            f"📨 **Новое сообщение от {sender_name}:**\n"
            f"```\n{text[:300]}{'...' if len(text) > 300 else ''}\n```\n\n"
            f"🤖 **AI-анализ и варианты ответа:**\n\n"
            f"{result}"
        )

        # Отправляем в "Избранное" (me)
        await client.send_message('me', notification, parse_mode='markdown')
        logger.info(f"Анализ отправлен в Избранное для сообщения от {sender_name}")
    except Exception as e:
        logger.error(f"Ошибка при анализе сообщения от {sender_name}: {e}")


async def main():
    """Основная функция userbot."""
    validate_userbot_config()

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    @client.on(events.NewMessage(incoming=True))
    async def handle_incoming(event):
        """Обрабатывает все входящие сообщения аккаунта."""
        try:
            # Игнорируем сообщения без текста
            text = event.message.text or event.message.caption or ''
            if not text or len(text) < MIN_TEXT_LENGTH:
                return

            # Игнорируем чаты из списка исключений
            chat_id = event.chat_id
            if chat_id in IGNORED_CHATS:
                return

            # Получаем отправителя
            sender = await event.get_sender()

            # Игнорируем сообщения от ботов
            if isinstance(sender, User) and sender.bot:
                return

            sender_name = format_sender_name(sender)
            logger.info(f"Новое сообщение от {sender_name}: {text[:50]}...")

            # Запускаем анализ в фоне (не блокируем обработку других событий)
            asyncio.create_task(
                analyze_and_notify(client, event, sender_name, text)
            )

        except Exception as e:
            logger.error(f"Ошибка при обработке входящего сообщения: {e}")

    print("Запуск userbot...")
    print("При первом запуске введи номер телефона и код подтверждения из Telegram.")
    print("Для остановки нажми Ctrl+C\n")

    async with client:
        me = await client.get_me()
        startup_msg = (
            f"✅ Userbot запущен для аккаунта: **{me.first_name}** (@{me.username or me.id})\n\n"
            f"Теперь все входящие сообщения длиннее {MIN_TEXT_LENGTH} символов будут "
            f"автоматически анализироваться. AI-ответы приходят сюда, в Избранное.\n\n"
            f"Чтобы добавить чат в игнор — отредактируй `IGNORED_CHATS` в `userbot.py`."
        )
        await client.send_message('me', startup_msg, parse_mode='markdown')
        logger.info(f"Userbot запущен для @{me.username or me.id}")

        await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
