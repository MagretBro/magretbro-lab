"""Генератор backend для сайта-портфолио через OpenRouter.

Первый этап генерирует только ядро backend:
- backend/main.py
- backend/services/ab_test.py
- backend/schemas/ab_test.py
- backend/requirements.txt

После успешной генерации можно отдельно сделать routers и projects.
"""

from __future__ import annotations

import pathlib
import sys
import threading
import time

import httpx
from openai import APIConnectionError, APITimeoutError, OpenAI

from config import API_KEY


# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

STAGE = "backend_core"

MODEL = "poolside/laguna-s-2.1"

TEMPERATURE = 0.2

# Пока специально не делаем огромный ответ.
MAX_TOKENS = 20000

RAW_OUTPUT = pathlib.Path(f"raw_output_{STAGE}.txt")
REASONING_LOG = pathlib.Path(f"reasoning_{STAGE}.log")
LOG_FILE = pathlib.Path(f"generate_{STAGE}.log")

# Не будем сидеть полчаса на одном запросе.
MAX_ATTEMPTS = 3

# Сколько символов предыдущего ответа передавать при продолжении.
CONTINUE_TAIL_CHARS = 6000

# Пауза между попытками.
BACKOFF_SECONDS = 5

# Heartbeat каждые 15 секунд.
HEARTBEAT_WAIT_SEC = 15


# ============================================================
# OPENROUTER CLIENT
# ============================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=httpx.Timeout(
        connect=30.0,
        read=300.0,
        write=60.0,
        pool=60.0,
    ),
)


# ============================================================
# PROMPT
# ============================================================

PROMPT = """
Ты senior Python backend developer.

Нужно создать минимальный, но полностью рабочий backend
для портфолио Data Analyst.

СТЕК:

- Python 3.10+
- FastAPI
- pandas
- numpy
- scipy
- pydantic
- uvicorn

ВАЖНО:

Сейчас НЕ нужно создавать весь сайт.

Создай только ядро backend.

Нужны ровно эти файлы:

=== FILE: backend/main.py ===

FastAPI application.

Требования:

- создать FastAPI app;
- добавить CORS для http://localhost:3000;
- добавить простой GET /api/health;
- endpoint должен возвращать:

{
    "status": "ok"
}

- подключить router A/B теста из backend.routers.ab_test.

=== FILE: backend/schemas/ab_test.py ===

Pydantic-схемы для API.

Нужны модели:

ABTestResponse.

В ответе должны быть:

group_a
group_b
n_a
n_b
conversions_a
conversions_b
conversion_a
conversion_b
absolute_diff
relative_uplift
z_statistic
p_value
significant

Все поля должны иметь понятные типы.

=== FILE: backend/services/ab_test.py ===

Вся математическая логика A/B-теста.

Создай функцию:

analyze_ab_test(
    df,
    group_column,
    metric_column
)

Она должна:

1. Проверить существование group_column.
2. Проверить существование metric_column.
3. Проверить отсутствие пропусков.
4. Проверить, что в группе ровно два уникальных значения.
5. Проверить, что метрика содержит только 0 и 1.
6. Определить группы A и B.
7. Посчитать количество наблюдений каждой группы.
8. Посчитать количество конверсий.
9. Посчитать conversion rate.
10. Посчитать absolute difference:

conversion_b - conversion_a

11. Посчитать relative uplift:

(conversion_b - conversion_a) / conversion_a

12. Выполнить z-test для двух пропорций.

Можно использовать scipy.

13. Вернуть результат в виде словаря.

При ошибках использовать ValueError с понятным текстом на русском языке.

Добавь docstring к функции.

=== FILE: backend/routers/ab_test.py ===

Создай FastAPI router.

Endpoint:

POST /api/ab-test/analyze

Принимает:

- CSV-файл через UploadFile;
- group_column;
- metric_column.

CSV необходимо прочитать через pandas.

Вызвать:

analyze_ab_test(...)

Вернуть результат через Pydantic-схему.

Ошибки валидации данных должны возвращать HTTP 400.

Ошибки параметров запроса должны возвращать HTTP 422 стандартными средствами FastAPI.

=== FILE: backend/requirements.txt ===

Добавь:

fastapi
uvicorn
pandas
numpy
scipy
python-multipart
pydantic

ТРЕБОВАНИЯ:

- код должен быть полностью рабочим;
- никаких TODO;
- никаких pass;
- никаких псевдокодов;
- все комментарии и сообщения об ошибках на русском;
- используй нормальную структуру импортов;
- не создавай лишние файлы;
- не объясняй решение.

ФОРМАТ ОТВЕТА СТРОГО:

=== FILE: backend/main.py ===
код

=== FILE: backend/schemas/ab_test.py ===
код

=== FILE: backend/services/ab_test.py ===
код

=== FILE: backend/routers/ab_test.py ===
код

=== FILE: backend/requirements.txt ===
код

=== ЗАПУСК ===
команды запуска backend

Не используй markdown fences внутри файлов.

Начинай сразу с:

=== FILE: backend/main.py ===
"""


# ============================================================
# LOGGING
# ============================================================

def log(message: str) -> None:
    """Выводит сообщение в терминал и записывает его в лог."""
    print(message, flush=True)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def log_reasoning(text: str) -> None:
    """Сохраняет reasoning модели в отдельный файл."""
    with REASONING_LOG.open("a", encoding="utf-8") as f:
        f.write(text)


# ============================================================
# PROGRESS
# ============================================================

def load_progress() -> str:
    """Загружает ранее сохранённый ответ."""
    if RAW_OUTPUT.exists():
        return RAW_OUTPUT.read_text(encoding="utf-8")

    return ""


def save_progress(text: str) -> None:
    """Атомарно сохраняет текущий прогресс."""
    tmp = RAW_OUTPUT.with_suffix(".tmp")

    tmp.write_text(
        text,
        encoding="utf-8",
    )

    tmp.replace(RAW_OUTPUT)


# ============================================================
# CONTINUATION PROMPT
# ============================================================

def build_continue_prompt(accumulated: str) -> str:
    """Формирует запрос на продолжение оборванной генерации."""

    tail = accumulated[-CONTINUE_TAIL_CHARS:]

    return f"""
Предыдущая генерация была прервана.

Продолжи генерацию РОВНО с места остановки.

Не повторяй уже написанный код.
Не объясняй решение.
Не начинай генерацию заново.

Вот последние символы уже полученного ответа:

=== BEGIN PREVIOUS OUTPUT ===

{tail}

=== END PREVIOUS OUTPUT ===

Продолжай прямо с места обрыва.
"""


# ============================================================
# HEARTBEAT
# ============================================================

def start_heartbeat(started_at: float):
    """Запускает периодический вывод статуса ожидания."""

    stop_event = threading.Event()

    state = {
        "content_seen": False,
    }

    def tick():
        while not stop_event.wait(HEARTBEAT_WAIT_SEC):

            elapsed = int(time.time() - started_at)

            if state["content_seen"]:
                log(
                    f"[waiting] {elapsed}s с начала запроса, "
                    f"получаю следующий chunk..."
                )
            else:
                log(
                    f"[waiting] {elapsed}s, "
                    f"content-чанков пока нет..."
                )

    thread = threading.Thread(
        target=tick,
        daemon=True,
    )

    thread.start()

    return stop_event, thread, state


# ============================================================
# STREAM
# ============================================================

def run_stream(
    accumulated: str,
    continuation: bool,
):
    """Запускает один streaming-запрос к OpenRouter."""

    if continuation:

        messages = [
            {
                "role": "user",
                "content": PROMPT,
            },
            {
                "role": "assistant",
                "content": accumulated,
            },
            {
                "role": "user",
                "content": build_continue_prompt(accumulated),
            },
        ]

    else:

        messages = [
            {
                "role": "user",
                "content": PROMPT,
            }
        ]

    started_at = time.time()

    stop_event, heartbeat_thread, state = start_heartbeat(
        started_at
    )

    log(
        f"[request] модель={MODEL}"
    )

    log(
        f"[request] этап={STAGE}"
    )

    log(
        "[request] отправляю запрос в OpenRouter..."
    )

    try:

        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=True,
            stream_options={
                "include_usage": True,
            },
        )

        log(
            "[request] соединение установлено, "
            "жду ответ..."
        )

        finish_reason = None

        content_chars = 0
        reasoning_chars = 0

        for chunk in stream:

            if not chunk.choices:

                if chunk.usage:

                    log("=== USAGE ===")

                    log(
                        f"prompt tokens: "
                        f"{chunk.usage.prompt_tokens}"
                    )

                    log(
                        f"completion tokens: "
                        f"{chunk.usage.completion_tokens}"
                    )

                    log(
                        f"total tokens: "
                        f"{chunk.usage.total_tokens}"
                    )

                continue

            choice = chunk.choices[0]

            delta = choice.delta

            # ------------------------------------------------
            # REASONING
            # ------------------------------------------------

            reasoning_piece = None

            for attr in (
                "reasoning",
                "reasoning_content",
            ):

                value = getattr(
                    delta,
                    attr,
                    None,
                )

                if value:
                    reasoning_piece = value
                    break

            if reasoning_piece:

                reasoning_chars += len(
                    reasoning_piece
                )

                log_reasoning(
                    reasoning_piece
                )

                if reasoning_chars % 500 < len(
                    reasoning_piece
                ):

                    log(
                        f"[reasoning] "
                        f"{reasoning_chars} символов"
                    )

            # ------------------------------------------------
            # CONTENT
            # ------------------------------------------------

            if delta and delta.content:

                if not state["content_seen"]:

                    state["content_seen"] = True

                    elapsed = int(
                        time.time() - started_at
                    )

                    log(
                        f"[first content] "
                        f"первый код через {elapsed}s"
                    )

                accumulated += delta.content

                content_chars += len(
                    delta.content
                )

                # Сохраняем примерно каждые 512 символов.
                if content_chars % 512 < len(
                    delta.content
                ):

                    save_progress(
                        accumulated
                    )

            if choice.finish_reason:

                finish_reason = (
                    choice.finish_reason
                )

        save_progress(accumulated)

        elapsed = int(
            time.time() - started_at
        )

        log(
            "=== FINISH ==="
        )

        log(
            f"finish_reason: {finish_reason}"
        )

        log(
            f"content: {content_chars} символов"
        )

        log(
            f"reasoning: {reasoning_chars} символов"
        )

        log(
            f"time: {elapsed}s"
        )

        return accumulated, finish_reason

    finally:

        stop_event.set()

        heartbeat_thread.join(
            timeout=1
        )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    log("")

    log("=" * 60)

    log(
        f"ЭТАП: {STAGE}"
    )

    log(
        f"МОДЕЛЬ: {MODEL}"
    )

    log("=" * 60)

    accumulated = load_progress()

    if accumulated:

        log(
            f"Найден существующий прогресс: "
            f"{len(accumulated)} символов."
        )

        log(
            "Будет выполнено продолжение."
        )

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):

        continuation = (
            bool(accumulated)
        )

        log("")

        log(
            f"--- Попытка "
            f"{attempt}/{MAX_ATTEMPTS} "
            f"({'продолжение' if continuation else 'с нуля'}) ---"
        )

        before = len(
            accumulated
        )

        try:

            accumulated, finish_reason = (
                run_stream(
                    accumulated,
                    continuation,
                )
            )

            growth = (
                len(accumulated)
                - before
            )

            log(
                f"Прирост: +{growth} символов"
            )

            # --------------------------------------------
            # Нормальное завершение
            # --------------------------------------------

            if finish_reason == "stop":

                log(
                    "Генерация завершена."
                )

                break

            # --------------------------------------------
            # Ответ упёрся в max_tokens
            # --------------------------------------------

            if finish_reason == "length":

                log(
                    "finish_reason='length'. "
                    "Ответ достиг max_tokens."
                )

                if growth == 0:

                    log(
                        "Нового текста не получено. "
                        "Останавливаю генерацию."
                    )

                    break

                continue

            # --------------------------------------------
            # Неизвестное завершение
            # --------------------------------------------

            log(
                f"Получен finish_reason={finish_reason}"
            )

            if growth == 0:

                log(
                    "Нового текста нет. "
                    "Останавливаю генерацию."
                )

                break

        except (
            APITimeoutError,
            APIConnectionError,
        ) as error:

            log(
                f"Обрыв: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            save_progress(
                accumulated
            )

            if attempt >= MAX_ATTEMPTS:

                log(
                    "Все попытки исчерпаны."
                )

                break

            log(
                f"Пауза "
                f"{BACKOFF_SECONDS} сек..."
            )

            time.sleep(
                BACKOFF_SECONDS
            )

        except KeyboardInterrupt:

            log(
                "[Ctrl+C] Остановка."
            )

            save_progress(
                accumulated
            )

            break

    # ========================================================
    # RESULT
    # ========================================================

    if not RAW_OUTPUT.exists():

        log(
            "Файл raw_output не создан."
        )

        return 1

    size = RAW_OUTPUT.stat().st_size

    reasoning_size = 0

    if REASONING_LOG.exists():

        reasoning_size = (
            REASONING_LOG.stat().st_size
        )

    log("")

    log("=" * 60)

    log(
        f"Готово. Сырой вывод:"
    )

    log(
        f"{RAW_OUTPUT} "
        f"({size} bytes)"
    )

    log(
        f"Reasoning:"
    )

    log(
        f"{REASONING_LOG} "
        f"({reasoning_size} bytes)"
    )

    log(
        f"Лог:"
    )

    log(
        f"{LOG_FILE}"
    )

    log("=" * 60)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())