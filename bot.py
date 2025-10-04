#!/usr/bin/env python3
"""
Telegram Bot @bervich_bot
Основной файл для работы с Telegram Bot API
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}!\n"
        f"Я бот @bervich_bot. Рад видеть тебя!\n\n"
        f"Доступные команды:\n"
        f"/start - начать работу с ботом\n"
        f"/help - показать справку\n"
        f"/info - информация о боте"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
🤖 Помощь по боту @bervich_bot

Доступные команды:
/start - начать работу с ботом
/help - показать эту справку
/info - информация о боте

Просто отправь мне любое сообщение, и я отвечу!
    """
    await update.message.reply_text(help_text)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /info"""
    info_text = """
ℹ️ Информация о боте

Имя: @bervich_bot
Создатель: bervin00-sudo
Версия: 1.0
Статус: Активен

Этот бот создан для демонстрации работы с Telegram Bot API.
    """
    await update.message.reply_text(info_text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    response = f"Вы написали: {user_message}\n\nЯ получил ваше сообщение! 👍"
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.warning(f'Update {update} caused error {context.error}')

def main() -> None:
    """Основная функция для запуска бота"""
    
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Ошибка: Не установлен токен бота!")
        print("Получите токен у @BotFather и установите переменную окружения BOT_TOKEN")
        return
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))
    
    # Добавление обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Добавление обработчика ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    print("🚀 Запуск бота @bervich_bot...")
    print("Для остановки нажмите Ctrl+C")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
