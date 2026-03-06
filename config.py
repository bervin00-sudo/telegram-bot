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

# Настройки Claude AI
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

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
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "❌ Ошибка конфигурации: Не установлен ключ Anthropic API!\n"
            "Получите ключ на console.anthropic.com и установите переменную ANTHROPIC_API_KEY"
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
