"""
AI-ассистент для анализа сообщений и генерации ответов с помощью Claude.
"""

import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — умный ассистент для помощи в общении в Telegram.
Твоя задача — анализировать входящие сообщения и помогать пользователю формулировать грамотные,
корректные и эффективные ответы.

При анализе сообщений и генерации ответов ты должен:
- Учитывать тон и контекст сообщения (деловой, дружеский, нейтральный)
- Предлагать несколько вариантов ответа разной длины и стиля
- Следить за политической и социальной корректностью
- Избегать оскорбительных, дискриминирующих или провокационных формулировок
- Сохранять конструктивность и уважительность в любой ситуации

Отвечай всегда на русском языке, если не указано иное."""


def analyze_message(message_text: str) -> str:
    """
    Анализирует входящее сообщение и предлагает варианты ответа.

    Args:
        message_text: Текст входящего сообщения для анализа

    Returns:
        Текст с анализом и вариантами ответа
    """
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Проанализируй это входящее сообщение и предложи 3 варианта ответа:

Сообщение: {message_text}

Структура ответа:
1. Краткий анализ тона и намерения сообщения (1-2 предложения)
2. Три варианта ответа:
   - Вариант 1 (краткий, формальный)
   - Вариант 2 (развёрнутый, дружеский)
   - Вариант 3 (нейтральный, по существу)"""
            }
        ]
    ) as stream:
        return stream.get_final_message().content[-1].text


def generate_reply(context: str, instructions: str = "") -> str:
    """
    Помогает сформулировать ответ на основе контекста.

    Args:
        context: Контекст переписки или описание ситуации
        instructions: Дополнительные инструкции по стилю/тону ответа

    Returns:
        Готовый текст ответа
    """
    user_prompt = f"Помоги сформулировать ответ для следующей ситуации:\n\n{context}"
    if instructions:
        user_prompt += f"\n\nДополнительные требования: {instructions}"

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    ) as stream:
        return stream.get_final_message().content[-1].text


def analyze_chain(messages: list[dict]) -> str:
    """
    Анализирует цепочку сообщений и предлагает ответ на последнее.

    Args:
        messages: список {'sender': str, 'text': str} в хронологическом порядке

    Returns:
        Анализ разговора и варианты ответа
    """
    formatted = '\n'.join(
        f"{m['sender']}: {m['text']}" for m in messages
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1500,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Проанализируй эту цепочку сообщений и предложи варианты ответа на последнее сообщение.

Цепочка переписки:
{formatted}

Структура ответа:
1. Краткое резюме разговора (2-3 предложения)
2. Анализ последнего сообщения: тон, намерение, что требует ответа
3. Три варианта ответа на последнее сообщение:
   - Вариант 1 (краткий, формальный)
   - Вариант 2 (развёрнутый, дружеский)
   - Вариант 3 (нейтральный, по существу)"""
            }
        ]
    ) as stream:
        return stream.get_final_message().content[-1].text


def check_reply(reply_text: str) -> str:
    """
    Проверяет предложенный ответ на политкорректность и корректность.

    Args:
        reply_text: Текст ответа для проверки

    Returns:
        Результат проверки с оценкой и рекомендациями
    """
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Проверь следующий текст на политкорректность, уважительность и уместность:

Текст для проверки:
\"{reply_text}\"

Оцени по следующим критериям:
1. Политкорректность (есть ли дискриминирующие формулировки?)
2. Уважительность (соблюдается ли уважение к собеседнику?)
3. Тон (насколько уместен тон для деловой/дружеской переписки?)
4. Ясность (понятно ли изложена мысль?)

Дай общую оценку: ✅ Готово к отправке / ⚠️ Требует правок / ❌ Не рекомендуется.
Если требуются правки — предложи улучшенный вариант."""
            }
        ]
    ) as stream:
        return stream.get_final_message().content[-1].text
