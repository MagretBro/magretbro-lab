import os
from openai import OpenAI
from dotenv import load_dotenv
from config import API_KEY

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=900.0,
)

prompt = """
У тебя есть задача превратить существующее локальное Streamlit-приложение
(анализ A/B-теста) в полноценный сайт-портфолио с разделённым backend и frontend.

Сайт должен презентовать меня как специалиста по двум направлениям:
- Analytics (продуктовая и статистическая аналитика)
- AI Engineering (LLM-приложения, RAG, агенты, интеграции с API)

Цель сайта: привлечь HR-специалистов и потенциальных клиентов.

СТЕК:
Backend:
- Python 3.11+
- FastAPI + uvicorn
- pandas, numpy, scipy (для A/B-теста)
- pydantic для схем ответов
- CORS настроен для localhost:3000

Frontend:
- Next.js 14 (App Router), TypeScript
- Tailwind CSS + shadcn/ui
- Recharts или Plotly.js для графиков
- fetch к backend на http://localhost:8000
- Никаких Docker, БД и авторизации.

СТРУКТУРА ПРОЕКТА (обязательно):

backend/
  main.py               — FastAPI app, CORS, подключение роутеров
  routers/
    ab_test.py          — POST /api/ab-test/analyze (принимает CSV)
    projects.py         — GET /api/projects (читает data/projects.json)
  services/
    ab_test.py          — вся логика A/B-анализа (вынести из старого скрипта)
  schemas/
    ab_test.py          — pydantic-модели запроса/ответа
  data/
    projects.json       — данные о мини-проектах

frontend/
  app/
    layout.tsx          — общий layout, navbar, footer
    page.tsx            — главная (краткое позиционирование + CTA)
    about/page.tsx
    analytics/page.tsx  — описание + форма загрузки CSV + вызов API
    ai/page.tsx
    projects/page.tsx   — карточки, данные из GET /api/projects
    contact/page.tsx
  components/
    Navbar.tsx
    Footer.tsx
    ProjectCard.tsx
    ABTestForm.tsx      — загрузка CSV, вывод результата, график
  lib/
    api.ts              — обёртки fetch к backend
  public/
    resume.pdf          — заглушка

README.md               — как запустить backend и frontend
requirements.txt        — зависимости backend
package.json            — уже сгенерируется Next.js, укажи зависимости

ТРЕБОВАНИЯ К СТРАНИЦАМ:

1. /about
   - Позиционирование (1 абзац).
   - Блок "Направления": Analytics и AI Engineering, по 3-4 пункта.
   - Блок "Скиллы" с бейджами.
   - Кнопка "Скачать резюме" (ссылка на /resume.pdf).

2. /analytics
   - Описание направления.
   - Секция "Live demo": форма загрузки CSV, выбор колонок группы и метрики,
     отправка на POST /api/ab-test/analyze.
   - Отображение результата: размеры групп, конверсии, absolute diff,
     relative uplift, z-statistic, p-value, вывод о значимости при alpha=0.05.
   - График конверсии A и B (Recharts или Plotly.js).

3. /ai
   - Описание направления: LLM-приложения, RAG, агенты, prompt engineering.
   - Список технологий.
   - 2-3 мини-кейса текстом.

4. /projects
   - Забирает данные с GET /api/projects.
   - Рендерит карточки: название, описание, стек, ссылка.

5. /contact
   - Email, Telegram, GitHub, LinkedIn (placeholders).
   - CTA "Открыт к предложениям и заказам".
   - Форма обратной связи (без реальной отправки, вывести alert).

ТРЕБОВАНИЯ К КОДУ:
- Backend: типизация через pydantic, docstring у функций, обработка ошибок
  (невалидный CSV, отсутствующие колонки, пропуски) с понятными HTTP-кодами.
- Frontend: типизация TypeScript, клиентские компоненты там, где нужны хуки.
- Все тексты — на русском, осмысленные, не Lorem ipsum.
- Никаких TODO и pass.

ФОРМАТ ОТВЕТА:
Выводи файлы так, без лишних объяснений:

=== FILE: backend/main.py ===
<содержимое>

=== FILE: frontend/app/page.tsx ===
<содержимое>

... и так далее для всех файлов.

В конце блок "=== ЗАПУСК ===" с командами для backend и frontend.

Не используй Markdown-разметку внутри кода.
Не объясняй решение.
"""
stream = client.chat.completions.create(
    model="stealth/space-bunny-alpha",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.2,
    max_tokens=20000,
    stream=True,
    stream_options={
        "include_usage": True
    },
)

output_file = "app.py"

with open(output_file, "w", encoding="utf-8") as f:
    for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content

            if content:
                f.write(content)
                f.flush()

        if chunk.usage:
            print("\n\n=== USAGE ===")
            print("prompt tokens:", chunk.usage.prompt_tokens)
            print("completion tokens:", chunk.usage.completion_tokens)
            print("total tokens:", chunk.usage.total_tokens)

        if chunk.choices:
            finish_reason = chunk.choices[0].finish_reason

            if finish_reason:
                print("\n=== FINISH REASON ===")
                print(finish_reason)

print(f"\nРезультат сохранён в {output_file}")