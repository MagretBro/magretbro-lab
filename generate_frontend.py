import os
import re
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise RuntimeError("Не найден OPENROUTER_API_KEY в .env")


MODEL = "poolside/laguna-s-2.1"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    timeout=300.0,
)


# ============================================================
# ЭТАПЫ ГЕНЕРАЦИИ
# ============================================================

STAGES = {
    "1": {
        "name": "frontend core",
        "description": "Базовый Next.js каркас",
        "files": [
            "frontend/package.json",
            "frontend/tsconfig.json",
            "frontend/next.config.ts",
            "frontend/.gitignore",
            "frontend/app/layout.tsx",
            "frontend/app/globals.css",
            "frontend/app/page.tsx",
            "frontend/components/Navbar.tsx",
            "frontend/components/Footer.tsx",
        ],
    },

    "2": {
        "name": "frontend pages",
        "description": "Основные страницы портфолио",
        "files": [
            "frontend/app/about/page.tsx",
            "frontend/app/analytics/page.tsx",
            "frontend/app/ai/page.tsx",
            "frontend/app/projects/page.tsx",
            "frontend/app/contact/page.tsx",
            "frontend/lib/api.ts",
        ],
    },

    "3": {
        "name": "ab test demo",
        "description": "Интерактивный A/B Test",
        "files": [
            "frontend/components/ABTestForm.tsx",
            "frontend/components/ABTestResults.tsx",
            "frontend/app/analytics/ab-test/page.tsx",
        ],
    },
}


# ============================================================
# ПРОМПТЫ
# ============================================================

BASE_CONTEXT = """
Ты senior frontend developer.

Мы создаём frontend для портфолио Data Analyst.

Технологии:

- Next.js
- TypeScript
- React
- App Router
- обычный CSS
- без Tailwind
- без UI-библиотек

Backend уже существует отдельно на FastAPI:

http://localhost:8000

Backend НЕ нужно создавать.

Frontend должен работать:

npm install
npm run dev

и открываться:

http://localhost:3000

Важно:

Не придумывай дополнительные технологии.
Не добавляй authentication.
Не добавляй database.
Не добавляй Docker.
Не добавляй backend.

Стиль:

- современный
- минималистичный
- профессиональный
- портфолио Data Analyst
- хорошая типографика
- много воздуха
- аккуратные карточки
- адаптивность
"""


PROMPTS = {}


PROMPTS["1"] = BASE_CONTEXT + r"""

Сейчас генерируем ТОЛЬКО первый этап.

Нужен базовый рабочий frontend-каркас.

Создай только следующие файлы:

frontend/package.json
frontend/tsconfig.json
frontend/next.config.ts
frontend/.gitignore
frontend/app/layout.tsx
frontend/app/globals.css
frontend/app/page.tsx
frontend/components/Navbar.tsx
frontend/components/Footer.tsx

Главная страница должна содержать:

Маргарита Бородина

Data Analyst / Product Analyst

Data Analytics • Product Analytics • A/B Testing • SQL • Python

И четыре направления:

- SQL & Data
- Product Analytics
- A/B Testing
- Automation

Добавь навигацию:

Главная
Обо мне
Аналитика
AI
Проекты
Контакты

Пока ссылки могут вести на будущие страницы.

Главная должна быть полноценной красивой страницей, а не заглушкой.

Navbar и Footer должны быть переиспользуемыми компонентами.

CSS должен быть полностью рабочим.

Не используй изображения.

Не используй внешние API.

ВАЖНО:

Ответ должен содержать ТОЛЬКО файлы.

Формат:

=== FILE: frontend/package.json ===
полное содержимое

=== FILE: frontend/tsconfig.json ===
полное содержимое

...

=== END ===

Никаких пояснений до или после файлов.
"""


PROMPTS["2"] = BASE_CONTEXT + r"""

Первый этап frontend уже создан.

Сейчас генерируем ТОЛЬКО второй этап.

Создай следующие файлы:

frontend/app/about/page.tsx
frontend/app/analytics/page.tsx
frontend/app/ai/page.tsx
frontend/app/projects/page.tsx
frontend/app/contact/page.tsx
frontend/lib/api.ts

Страница About:

Покажи профессиональный путь:

DWH / ETL → Data Analytics → Product Analytics → Development → Data Analytics

Не придумывай конкретные компании, цифры или достижения.

Страница Analytics:

Заголовок:

A/B Test Analytics

Описание:

Интерактивный анализ A/B-теста с загрузкой CSV.

Добавь кнопку:

Открыть A/B Test Demo

Она должна вести на:

/analytics/ab-test

Страница AI:

Заглушка для AI-проектов.

Страница Projects:

Покажи:

A/B Test Quality Control
A/B Test Analytics
RAG Chatbot

Не придумывай дополнительные факты.

Страница Contact:

Простая профессиональная контактная страница.

Создай:

frontend/lib/api.ts

В нём подготовь типизированную функцию:

analyzeABTest(file, groupColumn, metricColumn)

Она должна отправлять:

POST http://localhost:8000/api/ab-test/analyze

через FormData.

Тип ответа:

{
  group_a: string;
  group_b: string;
  n_a: number;
  n_b: number;
  conversions_a: number;
  conversions_b: number;
  conversion_a: number;
  conversion_b: number;
  absolute_diff: number;
  relative_uplift: number;
  z_statistic: number;
  p_value: number;
  significant: boolean;
}

ВАЖНО:

Ответ должен содержать ТОЛЬКО файлы.

Формат:

=== FILE: frontend/app/about/page.tsx ===
полное содержимое

...

=== END ===
"""


PROMPTS["3"] = BASE_CONTEXT + r"""

Первый и второй этапы frontend уже созданы.

Сейчас генерируем ТОЛЬКО третий этап:

интерактивный A/B Test Demo.

Создай только:

frontend/components/ABTestForm.tsx
frontend/components/ABTestResults.tsx
frontend/app/analytics/ab-test/page.tsx

Форма должна позволять:

1. загрузить CSV;
2. указать название колонки группы;
3. указать название бинарной метрики;
4. отправить данные на FastAPI;
5. показать состояние загрузки;
6. показать ошибку;
7. показать результат.

Используй существующую функцию:

analyzeABTest()

из:

frontend/lib/api.ts

Backend endpoint:

POST http://localhost:8000/api/ab-test/analyze

После успешного ответа покажи:

Group A
Group B
Размер выборки A
Размер выборки B
Конверсии A
Конверсии B
Conversion A
Conversion B
Absolute Difference
Relative Uplift
Z-statistic
P-value
Statistical significance

Не делай пока графики.

Не используй Recharts.

Не добавляй новые библиотеки.

Интерфейс должен быть аккуратным и понятным.

ВАЖНО:

Ответ должен содержать ТОЛЬКО файлы.

Формат:

=== FILE: frontend/components/ABTestForm.tsx ===
полное содержимое

=== FILE: frontend/components/ABTestResults.tsx ===
полное содержимое

=== FILE: frontend/app/analytics/ab-test/page.tsx ===
полное содержимое

=== END ===
"""


# ============================================================
# ПАРСИНГ ФАЙЛОВ
# ============================================================

def extract_complete_files(buffer):
    """
    Ищет только полностью завершённые FILE-блоки.

    Незаконченный последний файл НЕ записывается,
    чтобы не получить битый файл.
    """

    pattern = (
        r"=== FILE: (.+?) ===\s*\n"
        r"(.*?)(?=\n=== FILE: |\n=== END ===)"
    )

    matches = re.findall(pattern, buffer, re.DOTALL)

    return [
        (path.strip(), content.strip())
        for path, content in matches
    ]


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def save_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")

    print()
    print(f"  ✓ СОХРАНЁН: {path}")
    print()


# ============================================================
# ГЕНЕРАЦИЯ ЭТАПА
# ============================================================

def generate_stage(stage_number):

    stage = STAGES[stage_number]
    prompt = PROMPTS[stage_number]

    print()
    print("=" * 60)
    print(f"ЭТАП {stage_number}: {stage['name']}")
    print(stage["description"])
    print("=" * 60)
    print()

    print("Файлы:")
    for file_path in stage["files"]:
        print(f"  - {file_path}")

    print()
    print(f"Model: {MODEL}")
    print("Отправляю запрос...")
    print()

    start = time.time()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
            max_tokens=12000,
            stream=True,
        )

    except Exception as e:
        print()
        print("❌ Ошибка при подключении к OpenRouter:")
        print(e)
        return False

    print("[stream] Соединение установлено.")
    print("[stream] Начинаю получать ответ...")
    print()

    buffer = ""
    saved_files = set()

    stream_file = f".frontend_stage_{stage_number}.stream"

    try:
        with open(stream_file, "w", encoding="utf-8") as debug_file:

            for chunk in response:

                try:
                    delta = chunk.choices[0].delta.content
                except (AttributeError, IndexError):
                    delta = None

                if not delta:
                    continue

                buffer += delta

                # Сохраняем абсолютно всё, что пришло
                debug_file.write(delta)
                debug_file.flush()

                # Показываем прогресс
                print(delta, end="", flush=True)

                # Ищем уже полностью полученные файлы
                complete_files = extract_complete_files(buffer)

                for path, content in complete_files:

                    if path in saved_files:
                        continue

                    if path not in stage["files"]:
                        continue

                    save_file(path, content)

                    saved_files.add(path)

    except Exception as e:

        elapsed = time.time() - start

        print()
        print()
        print("=" * 60)
        print("⚠️ STREAM ПРЕРВАН")
        print("=" * 60)
        print()
        print(f"Время работы: {elapsed:.1f} сек.")
        print(f"Уже сохранено файлов: {len(saved_files)}")
        print(f"Промежуточный ответ: {stream_file}")
        print()
        print("Ошибка:")
        print(e)
        print()

        if saved_files:
            print("Уже полученные файлы НЕ потеряны.")

        print()
        print("Можно запустить этот этап повторно.")
        print()

        return False

    elapsed = time.time() - start

    print()
    print()
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    print()
    print(f"Время: {elapsed:.1f} сек.")
    print(f"Сохранено файлов: {len(saved_files)} / {len(stage['files'])}")
    print()

    missing = [
        path
        for path in stage["files"]
        if path not in saved_files
    ]

    if missing:
        print("⚠️ Не получены:")
        for path in missing:
            print(f"  - {path}")

        print()

        print(
            "Ответ сохранён в:",
            stream_file
        )

        return False

    print("✓ Все файлы этапа созданы.")
    print()

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print()
        print("Использование:")
        print()
        print("  python generate_frontend.py 1")
        print("  python generate_frontend.py 2")
        print("  python generate_frontend.py 3")
        print()

        print("Этапы:")
        print("  1 — frontend core")
        print("  2 — страницы")
        print("  3 — A/B Test Demo")
        print()

        return

    stage_number = sys.argv[1]

    if stage_number not in STAGES:
        print(f"Неизвестный этап: {stage_number}")
        return

    success = generate_stage(stage_number)

    if success:

        if stage_number == "1":

            print("Следующий шаг:")
            print()
            print("cd frontend")
            print("npm install")
            print("npm run dev")
            print()

        elif stage_number == "2":

            print("Этап 2 готов.")
            print()

        elif stage_number == "3":

            print("A/B Test Demo готов.")
            print()


if __name__ == "__main__":
    main()