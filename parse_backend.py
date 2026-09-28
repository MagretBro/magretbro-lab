from pathlib import Path
import re


INPUT = Path("raw_output_backend_core.txt")


def main():
    if not INPUT.exists():
        print(f"Файл не найден: {INPUT}")
        return

    text = INPUT.read_text(encoding="utf-8")

    # Находим все блоки вида:
    # === FILE: backend/main.py ===
    # ...
    pattern = (
        r"=== FILE: (.+?) ===\s*\n"
        r"(.*?)(?=\n=== FILE: |\n=== ЗАПУСК ===|\Z)"
    )

    matches = re.findall(
        pattern,
        text,
        flags=re.DOTALL,
    )

    if not matches:
        print("Файлы в ответе модели не найдены.")
        return

    for file_path, content in matches:

        file_path = file_path.strip()
        content = content.strip()

        # Убираем markdown fences:
        content = re.sub(
            r"^```(?:python|text|bash)?\s*",
            "",
            content,
        )

        content = re.sub(
            r"\s*```$",
            "",
            content,
        )

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            content.strip() + "\n",
            encoding="utf-8",
        )

        print(f"Создан: {path}")

    # Создаём __init__.py для Python-пакетов.
    packages = [
        Path("backend"),
        Path("backend/routers"),
        Path("backend/schemas"),
        Path("backend/services"),
    ]

    for package in packages:
        package.mkdir(
            parents=True,
            exist_ok=True,
        )

        init_file = package / "__init__.py"

        if not init_file.exists():
            init_file.write_text(
                "",
                encoding="utf-8",
            )

            print(f"Создан: {init_file}")

    print()
    print("Готово.")


if __name__ == "__main__":
    main()
