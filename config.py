"""
Конфигурация для Telegram Bot @bervich_bot
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
BOT_USERNAME = '@bervich_bot'
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Проверка обязательных настроек
def validate_config():
    """Проверка корректности конфигурации"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        raise ValueError(
            "❌ Ошибка конфигурации: Не установлен токен бота!\n"
            "Получите токен у @BotFather и установите переменную BOT_TOKEN"
        )
    return True

# Информация о боте
BOT_INFO = {
    'name': 'bervich_bot',
    'version': '1.0.0',
    'author': 'bervin00-sudo',
    'description': 'Telegram Bot для демонстрации работы с Bot API',
    'commands': [
        '/start - начать работу с ботом',
        '/help - показать справку',
        '/info - информация о боте'
    ]
}
