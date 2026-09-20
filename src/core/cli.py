# src/core/cli.py
"""CLI-команды для core-package.

Команда core-init инициализирует проект с шаблонами и примерами.
"""

import argparse
from pathlib import Path
from importlib import resources


def _copy_template(template_name: str, dest: Path, force: bool = False) -> str:
    """Копирует шаблон из пакета в указанное место.

    Returns:
        "ok" — успешно создан, "exists" — файл уже был, "error" — ошибка чтения шаблона.
    """
    if dest.exists() and not force:
        print(f"Файл {dest} уже существует. Используйте --force для перезаписи.")
        return "exists"

    try:
        content = resources.read_text("core", f"templates/{template_name}", encoding="utf-8")
    except Exception:
        try:
            content = resources.files("core").joinpath(f"templates/{template_name}").read_text(encoding="utf-8")
        except Exception as e:
            print(f"Ошибка чтения шаблона {template_name}: {e}")
            return "error"

    dest.write_text(content, encoding="utf-8")
    print(f"Создан: {dest}")
    return "ok"


def _ensure_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True)
        print(f"Создана папка: {path}")


def init() -> None:
    parser = argparse.ArgumentParser(description="Инициализация проекта с core-package")
    parser.add_argument("--force", action="store_true", help="Перезаписать существующие файлы")
    parser.add_argument(
        "--target-dir",
        default="core_project",
        help="Папка для кода (по умолчанию: core_project)",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    force = args.force
    target_path = cwd / args.target_dir

    # 1. Конфиг
    env_status = _copy_template("env_template.txt", cwd / ".core-package.env", force)

    # 2. Папки пользовательского кода
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

    # 3. Примеры
    examples_dir = target_path / "examples"
    _ensure_dir(examples_dir)

    template_errors = []
    for tpl, dest_name in [
        ("scenario_template.py", "example_scenario.py"),
        ("main_template.py", "main_example.py"),
        ("main_with_event_infra_template.py", "main_with_event_infra_example.py"),
        ("examples_readme_template.md", "README.md"),
    ]:
        result = _copy_template(tpl, examples_dir / dest_name, force)
        if result == "error":
            template_errors.append(tpl)

    # 4. pyproject.toml
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
        print(f"Файл {pyproject} уже существует, пропускаем (--force для перезаписи).")

    # 5. README
    readme_project = cwd / "README.md"
    if not readme_project.exists() or force:
        content = (
            '# Мой проект на core-package\n'
            '\n'
            '## Установка\n\n```bash\npip install -e .\n```\n'
            '\n## Использование\n\n'
            f'Примеры в `{args.target_dir}/examples/`:\n'
            '\n'
            f'- `main_example.py` — in-memory демо без event-infra\n'
            f'- `main_with_event_infra_example.py` — связка с event-infra\n'
            '\n```bash\n'
            f'python {args.target_dir}/examples/main_example.py\n'
            '```\n'
        )
        readme_project.write_text(content, encoding="utf-8")
        print(f"Создан: {readme_project}")
    else:
        print(f"Файл {readme_project} уже существует, пропускаем (--force для перезаписи).")

    print("\nИнициализация завершена:")
    if env_status == "error":
        print("  ВНИМАНИЕ: не удалось создать .core-package.env")
    if template_errors:
        print(f"  ВНИМАНИЕ: не удалось скопировать шаблоны: {', '.join(template_errors)}")
    print("  1. Отредактируйте .core-package.env.")
    print(f"  2. Изучите примеры в {args.target_dir}/examples/.")
    print(f"  3. Запустите: python {args.target_dir}/examples/main_example.py")
