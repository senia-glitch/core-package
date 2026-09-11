# src/core/cli.py
"""CLI-команды для core-package.

Команда core-init инициализирует проект с шаблонами и примерами.
"""

import argparse
from pathlib import Path
from importlib import resources


def _copy_template(template_name: str, dest: Path, force: bool = False) -> bool:
    """Копирует шаблон из пакета в указанное место."""
    if dest.exists() and not force:
        print(f"Файл {dest} уже существует. Используйте --force для перезаписи.")
        return False

    try:
        content = resources.read_text("core", f"templates/{template_name}", encoding="utf-8")
    except Exception as e:
        try:
            content = resources.files("core").joinpath(f"templates/{template_name}").read_text(encoding="utf-8")
        except Exception:
            print(f"Ошибка чтения шаблона {template_name}: {e}")
            return False

    dest.write_text(content, encoding="utf-8")
    print(f"Создан: {dest}")
    return True


def _ensure_dir(path: Path) -> None:
    """Создаёт директорию, если её нет."""
    if not path.exists():
        path.mkdir(parents=True)
        print(f"Создана папка: {path}")


def init() -> None:
    """Инициализация проекта: создаёт структуру папок и файлов."""
    parser = argparse.ArgumentParser(description="Инициализация проекта с core-package")
    parser.add_argument("--force", action="store_true", help="Перезаписать существующие файлы")
    parser.add_argument(
        "--target-dir",
        default="core_project",
        help="Папка, в которую будут помещены сгенерированные файлы (кроме .core-package.env). По умолчанию: core_project"
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    force = args.force
    target_path = cwd / args.target_dir

    # 1. Конфигурационный файл (всегда в текущей папке)
    _copy_template("env_template.txt", cwd / ".core-package.env", force)

    # 2. Папки для пользовательского кода внутри target_path
    for folder in ["scenarios", "interfaces", "utils"]:
        folder_path = target_path / folder
        _ensure_dir(folder_path)

        init_file = folder_path / "__init__.py"
        if not init_file.exists() or force:
            init_file.write_text("# Автоматически создано core-init\n", encoding="utf-8")
            print(f"Создан: {init_file}")

        readme = folder_path / "README.md"
        if not readme.exists() or force:
            readme.write_text(f"# {folder.capitalize()}\n\nЗдесь находятся ваши {folder}.\n", encoding="utf-8")
            print(f"Создан: {readme}")

    # 3. Примеры внутри target_path
    examples_dir = target_path / "examples"
    _ensure_dir(examples_dir)

    _copy_template("scenario_template.py", examples_dir / "example_scenario.py", force)
    _copy_template("adapter_template.py", examples_dir / "event_infra_adapter.py", force)
    _copy_template("main_template.py", examples_dir / "main_example.py", force)

    # 4. pyproject.toml (в корне проекта)
    pyproject = cwd / "pyproject.toml"
    if not pyproject.exists() or force:
        content = (
            '[project]\n'
            'name = "my-project"\n'
            'version = "0.1.0"\n'
            'description = "Мой проект на core-package"\n'
            'requires-python = ">=3.8"\n'
            'dependencies = [\n'
            '    "core-package",\n'
            ']\n'
        )
        pyproject.write_text(content, encoding="utf-8")
        print(f"Создан: {pyproject}")
    else:
        print(f"Файл {pyproject} уже существует, пропускаем (используйте --force для перезаписи).")

    # 5. README проекта (в корне)
    readme_project = cwd / "README.md"
    if not readme_project.exists() or force:
        content = (
            '# Мой проект на core-package\n'
            '\n'
            '## Установка\n'
            '\n'
            '```bash\n'
            'pip install -e .\n'
            '```\n'
            '\n'
            '## Использование\n'
            '\n'
            f'Смотрите примеры в папке `{args.target_dir}/examples/`.\n'
            'Запустите рабочий пример:\n'
            '```bash\n'
            f'python {args.target_dir}/examples/main_example.py\n'
            '```\n'
            '\n'
            '## Разработка\n'
            '\n'
            f'Добавляйте свои сценарии в папку `{args.target_dir}/scenarios/`.\n'
            'Помечайте класс декоратором `@register_scenario("имя")`.\n'
            'Сценарии подхватятся автоматически через `ScenarioRegistry.discover(...)`.\n'
        )
        readme_project.write_text(content, encoding="utf-8")
        print(f"Создан: {readme_project}")
    else:
        print(f"Файл {readme_project} уже существует, пропускаем (используйте --force для перезаписи).")

    print("\nИнициализация завершена. Теперь вы можете:")
    print("  1. Отредактировать .core-package.env под свои нужды.")
    print(f"  2. Изучить примеры в папке {args.target_dir}/examples/.")
    print(f"  3. Запустить рабочий пример: python {args.target_dir}/examples/main_example.py")
    print("  4. Начать разработку своих сценариев.")