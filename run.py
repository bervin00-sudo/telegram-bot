#!/usr/bin/env python3
"""
Единая точка запуска: Telegram Bot + Userbot работают вместе.

Запусти этот файл вместо bot.py или userbot.py:
    python run.py
"""

import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import bot as bot_module
import userbot as userbot_module
from telethon_client import get_client
from config import BOT_TOKEN, validate_userbot_config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    validate_userbot_config()

    # ── Telethon (userbot) ──────────────────────────────────────────
    telethon = get_client()
    userbot_module.register_handlers(telethon)

    await telethon.start()
    me = await telethon.get_me()
    logger.info(f"Userbot запущен как @{me.username or me.id}")

    await telethon.send_message(
        'me',
        f"✅ Запуск завершён. Userbot: **{me.first_name}**\n"
        f"Бот и userbot работают одновременно.",
        parse_mode='markdown'
    )

    # ── python-telegram-bot ─────────────────────────────────────────
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start",   bot_module.start))
    application.add_handler(CommandHandler("help",    bot_module.help_command))
    application.add_handler(CommandHandler("suggest", bot_module.suggest_command))
    application.add_handler(CommandHandler("draft",   bot_module.draft_command))
    application.add_handler(CommandHandler("check",   bot_module.check_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot_module.handle_message)
    )
    application.add_error_handler(bot_module.error_handler)

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=["message"])
    logger.info("Bot запущен")

    # Работаем пока userbot подключён
    await telethon.run_until_disconnected()

    # Graceful shutdown
    await application.updater.stop()
    await application.stop()
    await application.shutdown()


if __name__ == '__main__':
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("Ошибка: Не установлен BOT_TOKEN!")
    else:
        asyncio.run(main())
