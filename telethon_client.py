"""
Общий Telethon-клиент для доступа к Telegram User API.
Используется ботом (чтение сообщений по ссылке) и userbot (мониторинг).
"""

import re
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel, Message

from config import API_ID, API_HASH

SESSION_NAME = 'userbot_session'

# Единственный экземпляр клиента на весь процесс
_client: TelegramClient | None = None


def get_client() -> TelegramClient:
    global _client
    if _client is None:
        _client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    return _client


# Форматы ссылок:
#   https://t.me/c/1234567890/42   — приватный чат
#   https://t.me/username/42        — публичный чат/канал
_PRIVATE_LINK = re.compile(r'https?://t\.me/c/(\d+)/(\d+)')
_PUBLIC_LINK  = re.compile(r'https?://t\.me/([a-zA-Z][^/?#\s]*)/(\d+)')


def parse_message_link(url: str) -> tuple[str | int | None, int | None]:
    """
    Разбирает ссылку на сообщение Telegram.
    Возвращает (chat_ref, message_id) или (None, None).
    """
    m = _PRIVATE_LINK.search(url)
    if m:
        chat_id = int('-100' + m.group(1))
        return chat_id, int(m.group(2))

    m = _PUBLIC_LINK.search(url)
    if m:
        return m.group(1), int(m.group(2))

    return None, None


def format_sender(msg: Message) -> str:
    """Возвращает имя отправителя сообщения."""
    sender = msg.sender
    if isinstance(sender, User):
        name = ' '.join(p for p in [sender.first_name, sender.last_name] if p)
        return name or f"ID:{sender.id}"
    if isinstance(sender, (Chat, Channel)):
        return sender.title or f"Чат:{sender.id}"
    return "Неизвестный"


async def fetch_messages_from_link(
    url: str,
    limit: int = 40,
) -> tuple[str, list[dict]]:
    """
    Загружает сообщения из чата начиная с указанной в ссылке позиции.

    Возвращает (chat_title, messages_list).
    messages_list — список {'sender': str, 'text': str}.
    """
    chat_ref, msg_id = parse_message_link(url)
    if chat_ref is None:
        return "", []

    client = get_client()
    if not client.is_connected():
        await client.connect()

    entity = await client.get_entity(chat_ref)
    chat_title = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or str(chat_ref)

    # min_id включает сообщение с msg_id - 1 (Telethon не включает min_id сам по себе)
    raw_msgs = await client.get_messages(entity, min_id=msg_id - 1, limit=limit)
    raw_msgs = sorted(raw_msgs, key=lambda m: m.id)

    messages = [
        {
            'sender': format_sender(m),
            'text': (m.text or m.message or '').strip(),
        }
        for m in raw_msgs
        if (m.text or m.message or '').strip()
    ]

    return chat_title, messages
