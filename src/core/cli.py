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
    _copy_template("env_template.txt", cwd / ".core-package.env", force)

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

    _copy_template("scenario_template.py", examples_dir / "example_scenario.py", force)
    _copy_template("main_template.py", examples_dir / "main_example.py", force)
    _copy_template(
        "main_with_event_infra_template.py",
        examples_dir / "main_with_event_infra_example.py",
        force,
    )
    _copy_template(
        "examples_readme_template.md",
        examples_dir / "README.md",
        force,
    )

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
    print("  1. Отредактируйте .core-package.env.")
    print(f"  2. Изучите примеры в {args.target_dir}/examples/.")
    print(f"  3. Запустите: python {args.target_dir}/examples/main_example.py")