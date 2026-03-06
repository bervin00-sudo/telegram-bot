#!/usr/bin/env python3
"""
Telegram Bot @bervich_bot
AI-ассистент для мониторинга сообщений и помощи с ответами.
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import ai_assistant

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Хранилище последних сообщений пользователей (chat_id -> message_text)
last_messages: dict[int, str] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я твой AI-ассистент для переписки.\n\n"
        f"<b>Что я умею:</b>\n"
        f"• Анализировать сообщения и предлагать варианты ответа\n"
        f"• Помогать формулировать ответы\n"
        f"• Проверять текст на политкорректность\n\n"
        f"<b>Команды:</b>\n"
        f"/suggest — предложить варианты ответа на последнее сообщение\n"
        f"/draft [пожелания] — помочь написать ответ\n"
        f"/check [текст] — проверить текст на корректность\n"
        f"/help — справка\n\n"
        f"Перешли мне любое сообщение — я сразу его проанализирую!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "<b>Справка по командам:</b>\n\n"
        "<b>/suggest</b>\n"
        "Предлагает 3 варианта ответа на последнее входящее сообщение.\n"
        "Перешли нужное сообщение, затем используй /suggest.\n\n"
        "<b>/draft [пожелания]</b>\n"
        "Помогает сформулировать ответ. Перешли сообщение, затем:\n"
        "<code>/draft сделай ответ более официальным</code>\n\n"
        "<b>/check [текст]</b>\n"
        "Проверяет текст на политкорректность и уместность.\n"
        "<code>/check Привет! Можем встретиться завтра?</code>\n\n"
        "<b>Пересланные сообщения</b>\n"
        "Перешли любое сообщение — я автоматически его проанализирую."
    )
    await update.message.reply_html(help_text)


async def suggest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Предлагает варианты ответа на последнее сообщение пользователя."""
    chat_id = update.effective_chat.id
    message_text = last_messages.get(chat_id)

    if not message_text:
        await update.message.reply_text(
            "Нет сохранённого сообщения для анализа.\n"
            "Перешли мне сообщение, на которое хочешь ответить, и потом используй /suggest."
        )
        return

    thinking_msg = await update.message.reply_text("Анализирую сообщение...")

    try:
        result = ai_assistant.analyze_message(message_text)
        await thinking_msg.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка при анализе сообщения: {e}")
        await thinking_msg.edit_text("Произошла ошибка при анализе. Попробуй ещё раз.")


async def draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Помогает сформулировать ответ на последнее сообщение."""
    chat_id = update.effective_chat.id
    message_text = last_messages.get(chat_id)
    instructions = " ".join(context.args) if context.args else ""

    if not message_text:
        await update.message.reply_text(
            "Нет сохранённого сообщения.\n"
            "Перешли мне сообщение, на которое хочешь ответить, и потом используй /draft."
        )
        return

    context_text = f"Входящее сообщение: {message_text}"
    thinking_msg = await update.message.reply_text("Формулирую ответ...")

    try:
        result = ai_assistant.generate_reply(context_text, instructions)
        await thinking_msg.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {e}")
        await thinking_msg.edit_text("Произошла ошибка. Попробуй ещё раз.")


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет указанный текст на политкорректность."""
    if not context.args:
        await update.message.reply_text(
            "Укажи текст для проверки после команды.\n"
            "Пример: /check Привет! Можем встретиться завтра?"
        )
        return

    text_to_check = " ".join(context.args)
    thinking_msg = await update.message.reply_text("Проверяю текст...")

    try:
        result = ai_assistant.check_reply(text_to_check)
        await thinking_msg.delete()
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Ошибка при проверке текста: {e}")
        await thinking_msg.edit_text("Произошла ошибка при проверке. Попробуй ещё раз.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает входящие сообщения.
    Пересланные сообщения автоматически анализируются.
    Обычные сообщения сохраняются для последующего /suggest или /draft.
    """
    chat_id = update.effective_chat.id
    message = update.message

    # Определяем текст сообщения
    if message.forward_date or message.forward_from or message.forward_from_chat:
        # Пересланное сообщение — сразу анализируем
        message_text = message.text or message.caption or ""
        if not message_text:
            await message.reply_text("Не удалось извлечь текст из пересланного сообщения.")
            return

        last_messages[chat_id] = message_text
        thinking_msg = await message.reply_text(
            "Вижу пересланное сообщение. Анализирую..."
        )

        try:
            result = ai_assistant.analyze_message(message_text)
            await thinking_msg.delete()
            await message.reply_html(
                f"<b>Анализ пересланного сообщения:</b>\n\n{result}\n\n"
                f"Используй /draft для формулировки ответа или "
                f"/check чтобы проверить свой вариант."
            )
        except Exception as e:
            logger.error(f"Ошибка при анализе пересланного сообщения: {e}")
            await thinking_msg.edit_text(
                "Сообщение сохранено. Используй /suggest для анализа."
            )
    else:
        # Обычное сообщение — сохраняем как контекст
        message_text = message.text or ""
        last_messages[chat_id] = message_text
        await message.reply_text(
            "Сообщение сохранено как контекст.\n"
            "Используй:\n"
            "• /suggest — получить варианты ответа\n"
            "• /draft — сформулировать ответ\n"
            "• /check [текст] — проверить свой вариант"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.warning(f'Update {update} caused error {context.error}')


def main() -> None:
    """Основная функция для запуска бота"""

    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("Ошибка: Не установлен токен бота!")
        print("Получите токен у @BotFather и установите переменную окружения BOT_TOKEN")
        return

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("suggest", suggest_command))
    application.add_handler(CommandHandler("draft", draft_command))
    application.add_handler(CommandHandler("check", check_command))

    # Обработчик текстовых сообщений (включая пересылки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    print("Запуск AI-ассистента @bervich_bot...")
    print("Для остановки нажмите Ctrl+C")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
