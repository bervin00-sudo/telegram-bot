"""
База знаний: книги и инструкции, на которые опирается бот при формировании ответов.
Хранится в knowledge_base.json рядом со скриптом.
"""

import json
import os

_DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")

_DEFAULT = {"books": [], "instructions": []}


def _load() -> dict:
    if not os.path.exists(_DB_PATH):
        return {"books": [], "instructions": []}
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Книги ──────────────────────────────────────────────────────────────────

def add_book(title: str, description: str = "") -> int:
    """Добавляет книгу. Возвращает её id."""
    data = _load()
    next_id = max((b["id"] for b in data["books"]), default=0) + 1
    data["books"].append({"id": next_id, "title": title, "description": description})
    _save(data)
    return next_id


def delete_book(book_id: int) -> bool:
    """Удаляет книгу по id. Возвращает True если нашлась."""
    data = _load()
    before = len(data["books"])
    data["books"] = [b for b in data["books"] if b["id"] != book_id]
    _save(data)
    return len(data["books"]) < before


def list_books() -> list[dict]:
    return _load()["books"]


# ── Инструкции ─────────────────────────────────────────────────────────────

def add_instruction(text: str) -> int:
    """Добавляет инструкцию. Возвращает её порядковый номер (1-based)."""
    data = _load()
    data["instructions"].append(text)
    _save(data)
    return len(data["instructions"])


def delete_instruction(index: int) -> bool:
    """Удаляет инструкцию по номеру (1-based). Возвращает True если нашлась."""
    data = _load()
    if index < 1 or index > len(data["instructions"]):
        return False
    data["instructions"].pop(index - 1)
    _save(data)
    return True


def list_instructions() -> list[str]:
    return _load()["instructions"]


# ── Формирование контекста для промпта ────────────────────────────────────

def build_context_block() -> str:
    """
    Возвращает текстовый блок с книгами и инструкциями для вставки в системный промпт.
    Возвращает пустую строку, если база пуста.
    """
    data = _load()
    parts = []

    if data["books"]:
        books_text = "\n".join(
            f"  • {b['title']}" + (f" — {b['description']}" if b["description"] else "")
            for b in data["books"]
        )
        parts.append(f"Рекомендованные книги (опирайся на их подходы при формировании ответов):\n{books_text}")

    if data["instructions"]:
        instr_text = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(data["instructions"]))
        parts.append(f"Персональные инструкции (строго следуй им):\n{instr_text}")

    if not parts:
        return ""

    return "\n\n" + "\n\n".join(parts)
