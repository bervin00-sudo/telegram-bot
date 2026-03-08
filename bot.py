#!/usr/bin/env python3
"""
Telegram Bot @bervich_bot
AI-ассистент для мониторинга сообщений и помощи с ответами.
"""

import asyncio
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import ai_assistant
import telethon_client

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получить у @BotFather)
from config import BOT_TOKEN

# Хранилище последнего одиночного сообщения (chat_id -> text)
last_messages: dict[int, str] = {}

# Буфер пересланных цепочек: chat_id -> {'msgs': [{'sender','text'}], 'task': Task}
_forward_buffer: dict[int, dict] = {}

# Задержка сборки цепочки пересланных сообщений (сек)
CHAIN_COLLECT_DELAY = 2.0

# Регулярка для поиска ссылок t.me в тексте
_TME_LINK_RE = re.compile(r'https?://t\.me/\S+')


# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────

def _format_chain_text(messages: list[dict]) -> str:
    """Форматирует цепочку в читаемый вид для отображения."""
    lines = []
    for m in messages:
        text = m['text'][:120] + ('…' if len(m['text']) > 120 else '')
        lines.append(f"<b>{m['sender']}:</b> {text}")
    return '\n'.join(lines)


async def _run_analyze_message(text: str) -> str:
    """Запускает анализ одного сообщения в executor (синхронная функция)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, ai_assistant.analyze_message, text)


async def _run_analyze_chain(messages: list[dict]) -> str:
    """Запускает анализ цепочки в executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, ai_assistant.analyze_chain, messages)


# ──────────────────────────────────────────────
# Обработчик ссылки на сообщение в чате
# ──────────────────────────────────────────────

async def _handle_link(update: Update, url: str) -> None:
    """Читает сообщения из чата начиная с указанного по ссылке и анализирует."""
    msg = update.message
    status = await msg.reply_text("Читаю сообщения по ссылке…")

    try:
        chat_title, messages = await telethon_client.fetch_messages_from_link(url)
    except Exception as e:
        logger.error(f"Ошибка при получении сообщений по ссылке: {e}")
        await status.edit_text(f"Не удалось прочитать сообщения: {e}")
        return

    if not messages:
        await status.edit_text(
            "Не удалось загрузить сообщения.\n"
            "Проверь: userbot должен быть участником этого чата."
        )
        return

    await status.edit_text(
        f"Загружено {len(messages)} сообщений из «{chat_title}». Анализирую…"
    )

    try:
        result = await _run_analyze_chain(messages)
    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        await status.edit_text("Ошибка при анализе. Попробуй ещё раз.")
        return

    preview = _format_chain_text(messages[-5:])  # последние 5 для контекста
    await status.delete()
    await msg.reply_html(
        f"<b>Чат: {chat_title}</b> · {len(messages)} сообщений\n\n"
        f"<b>Последние сообщения:</b>\n{preview}\n\n"
        f"<b>AI-анализ и варианты ответа:</b>\n\n{result}"
    )


# ──────────────────────────────────────────────
# Обработчик цепочки пересланных сообщений
# ──────────────────────────────────────────────

async def _flush_forward_chain(chat_id: int, update: Update) -> None:
    """Вызывается после паузы — обрабатывает накопленную цепочку."""
    await asyncio.sleep(CHAIN_COLLECT_DELAY)

    entry = _forward_buffer.pop(chat_id, None)
    if not entry or not entry['msgs']:
        return

    messages = entry['msgs']
    msg = entry['last_update'].message

    status = await msg.reply_text(
        f"Получена цепочка из {len(messages)} сообщений. Анализирую…"
    )

    try:
        result = await _run_analyze_chain(messages)
    except Exception as e:
        logger.error(f"Ошибка анализа цепочки: {e}")
        await status.edit_text("Ошибка при анализе цепочки. Попробуй ещё раз.")
        return

    preview = _format_chain_text(messages)
    await status.delete()
    await msg.reply_html(
        f"<b>Цепочка: {len(messages)} сообщений</b>\n\n"
        f"{preview}\n\n"
        f"<b>AI-анализ и варианты ответа:</b>\n\n{result}"
    )


def _add_to_forward_buffer(chat_id: int, sender: str, text: str, update: Update):
    """Добавляет сообщение в буфер и (пере)запускает таймер сборки."""
    if chat_id not in _forward_buffer:
        _forward_buffer[chat_id] = {'msgs': [], 'task': None, 'last_update': update}

    _forward_buffer[chat_id]['msgs'].append({'sender': sender, 'text': text})
    _forward_buffer[chat_id]['last_update'] = update

    # Отменяем старый таймер и запускаем новый
    old_task = _forward_buffer[chat_id].get('task')
    if old_task and not old_task.done():
        old_task.cancel()

    task = asyncio.create_task(_flush_forward_chain(chat_id, update))
    _forward_buffer[chat_id]['task'] = task


# ──────────────────────────────────────────────
# Команды
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я твой AI-ассистент для переписки.\n\n"
        f"<b>Что я умею:</b>\n"
        f"• Анализировать одиночные и пересланные сообщения\n"
        f"• Читать цепочку сообщений по ссылке из чата\n"
        f"• Предлагать варианты ответа\n\n"
        f"<b>Как пользоваться:</b>\n"
        f"• Перешли одно сообщение — получи анализ\n"
        f"• Перешли несколько сообщений подряд — анализ всей цепочки\n"
        f"• Отправь ссылку t.me/… — бот прочитает чат с этого места\n\n"
        f"<b>Команды:</b>\n"
        f"/suggest — варианты ответа на последнее сообщение\n"
        f"/draft [пожелания] — сформулировать ответ\n"
        f"/check [текст] — проверить текст\n"
        f"/help — справка"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "<b>Справка:</b>\n\n"
        "<b>Ссылка на сообщение</b>\n"
        "Отправь ссылку вида <code>https://t.me/chatname/123</code> — бот загрузит "
        "сообщения начиная с этого места и предложит варианты ответа.\n\n"
        "<b>Цепочка пересланных сообщений</b>\n"
        "Перешли несколько сообщений подряд — бот соберёт их в цепочку и "
        "проанализирует разговор целиком.\n\n"
        "<b>/suggest</b> — варианты ответа на последнее сохранённое сообщение\n\n"
        "<b>/draft [пожелания]</b>\n"
        "<code>/draft сделай ответ официальнее</code>\n\n"
        "<b>/check [текст]</b>\n"
        "<code>/check Привет, как дела?</code>"
    )


async def suggest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message_text = last_messages.get(chat_id)
    if not message_text:
        await update.message.reply_text(
            "Нет сохранённого сообщения. Перешли мне сообщение и затем /suggest."
        )
        return

    status = await update.message.reply_text("Анализирую сообщение…")
    try:
        result = await _run_analyze_message(message_text)
        await status.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await status.edit_text("Ошибка при анализе. Попробуй ещё раз.")


async def draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message_text = last_messages.get(chat_id)
    instructions = " ".join(context.args) if context.args else ""

    if not message_text:
        await update.message.reply_text(
            "Нет сохранённого сообщения. Перешли мне сообщение и затем /draft."
        )
        return

    status = await update.message.reply_text("Формулирую ответ…")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, ai_assistant.generate_reply, f"Входящее сообщение: {message_text}", instructions
        )
        await status.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await status.edit_text("Ошибка. Попробуй ещё раз.")


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Укажи текст после команды.\nПример: /check Привет, как дела?"
        )
        return

    text_to_check = " ".join(context.args)
    status = await update.message.reply_text("Проверяю текст…")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, ai_assistant.check_reply, text_to_check)
        await status.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await status.edit_text("Ошибка при проверке. Попробуй ещё раз.")


# ──────────────────────────────────────────────
# Главный обработчик сообщений
# ──────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Логика обработки входящего сообщения:
    1. Если содержит ссылку t.me → читаем чат начиная с той позиции
    2. Если пересланное → добавляем в буфер цепочки
    3. Иначе → сохраняем как контекст для /suggest, /draft
    """
    message = update.message
    chat_id = update.effective_chat.id
    text = message.text or message.caption or ""

    # ── 1. Ссылка на сообщение в чате ──────────────────────────────
    link_match = _TME_LINK_RE.search(text)
    if link_match:
        await _handle_link(update, link_match.group(0))
        return

    # ── 2. Пересланное сообщение → цепочка ─────────────────────────
    is_forwarded = bool(
        message.forward_date
        or message.forward_from
        or message.forward_from_chat
        or message.forward_sender_name
    )

    if is_forwarded:
        if not text:
            await message.reply_text("Не удалось извлечь текст из пересланного сообщения.")
            return

        # Определяем имя оригинального отправителя
        if message.forward_from:
            u = message.forward_from
            parts = [u.first_name or '', u.last_name or '']
            sender_name = ' '.join(p for p in parts if p) or f"ID:{u.id}"
        elif message.forward_from_chat:
            sender_name = message.forward_from_chat.title or "Канал"
        elif message.forward_sender_name:
            sender_name = message.forward_sender_name
        else:
            sender_name = "Неизвестный"

        last_messages[chat_id] = text
        _add_to_forward_buffer(chat_id, sender_name, text, update)
        # Статус не показываем — покажет _flush_forward_chain после паузы
        return

    # ── 3. Обычное сообщение ────────────────────────────────────────
    last_messages[chat_id] = text
    await message.reply_text(
        "Сообщение сохранено.\n"
        "• /suggest — варианты ответа\n"
        "• /draft — сформулировать ответ\n"
        "• /check [текст] — проверить свой вариант"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} вызвал ошибку: {context.error}")


# ──────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────

def main() -> None:
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("Ошибка: Не установлен BOT_TOKEN!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("suggest", suggest_command))
    application.add_handler(CommandHandler("draft", draft_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    print("Запуск @bervich_bot…")
    print("Для остановки нажмите Ctrl+C")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
