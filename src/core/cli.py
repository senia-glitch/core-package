# src/core/cli.py
"""CLI-команды для core-package.

Команды:
- core-init — инициализация проекта с шаблонами и примерами.
- core-upgrade — обновление пакета до последней версии из GitHub.
"""

import argparse
import re
import shutil
import subprocess
import sys
import urllib.request
from importlib import resources
from pathlib import Path
from typing import Optional, Tuple

REPO_URL = "https://github.com/senia-glitch/core-package"
RAW_PYPROJECT_URL = (
    "https://raw.githubusercontent.com/senia-glitch/core-package/main/pyproject.toml"
)


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


# ============================================================
# core-upgrade
# ============================================================


def _get_local_version() -> str:
    """Возвращает текущую локальную версию пакета."""
    from importlib.metadata import version as get_version
    return get_version("core-package")


def _fetch_remote_pyproject() -> str:
    """Загружает raw pyproject.toml из main-ветки GitHub."""
    with urllib.request.urlopen(RAW_PYPROJECT_URL, timeout=15) as resp:
        return resp.read().decode("utf-8")


def _parse_version(toml_content: str) -> Optional[str]:
    """Извлекает строку version из содержимого pyproject.toml."""
    match = re.search(r'^version\s*=\s*"([^"]+)"', toml_content, re.MULTILINE)
    return match.group(1) if match else None


def _parse_requires_python(toml_content: str) -> Optional[str]:
    """Извлекает строку requires-python из содержимого pyproject.toml."""
    match = re.search(r'^requires-python\s*=\s*"([^"]+)"', toml_content, re.MULTILINE)
    return match.group(1) if match else None


def _version_to_tuple(version_str: str) -> Tuple[int, ...]:
    """Преобразует строку версии '0.2.0' в кортеж (0, 2, 0)."""
    return tuple(int(x) for x in version_str.strip().split("."))


def _parse_python_range(requires_python: str) -> Tuple[Optional[int], Optional[int]]:
    """Извлекает нижнюю и верхнюю границу из строкиrequires-python.

    Примеры:
        ">=3.8"        -> (3, None)
        ">=3.8,<4.0"   -> (3, 4)
        ">=3.9,<3.14"  -> (3, 3)
    """
    lower = None
    upper = None

    m_lower = re.search(r'>=\s*(\d+)', requires_python)
    if m_lower:
        lower = int(m_lower.group(1))

    m_upper = re.search(r'<\s*(\d+)', requires_python)
    if m_upper:
        upper = int(m_upper.group(1))

    return lower, upper


def _check_python_compatibility(requires_python: str) -> bool:
    """Проверяет, попадает ли текущая версия Python в диапазон requires-python.

    Returns:
        True — совместимо, False — несовместимо.
    """
    lower, upper = _parse_python_range(requires_python)
    current = sys.version_info.major

    if lower is not None and current < lower:
        return False
    if upper is not None and current >= upper:
        return False
    return True


def _find_pip() -> Optional[str]:
    """Находит исполняемый pip.

    Пробует:
    1. pip из PATH
    2. python -m pip
    3. sys.executable -m pip
    """
    # 1. pip из PATH
    pip_path = shutil.which("pip")
    if pip_path:
        return pip_path

    # 2. python -m pip
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            check=True,
        )
        return sys.executable
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None


def upgrade() -> None:
    """Обновляет core-package до последней версии из GitHub."""
    print("Проверка доступных обновлений...\n")

    # 1. Локальная версия
    try:
        local_version_str = _get_local_version()
    except Exception as e:
        print(f"Ошибка: не удалось определить текущую версию: {e}")
        sys.exit(1)

    local_version = _version_to_tuple(local_version_str)
    print(f"Текущая версия:  {local_version_str}")

    # 2. Удалённый pyproject.toml
    try:
        remote_toml = _fetch_remote_pyproject()
    except Exception as e:
        print(f"Ошибка: не удалось загрузить информацию о версии: {e}")
        print(f"Убедитесь, что репозиторий доступен: {REPO_URL}")
        sys.exit(1)

    remote_version_str = _parse_version(remote_toml)
    if not remote_version_str:
        print("Ошибка: не удалось извлечь версию из удалённого pyproject.toml")
        sys.exit(1)

    remote_version = _version_to_tuple(remote_version_str)
    print(f"Доступная версия: {remote_version_str}")

    # 3. Сравнение версий
    if local_version >= remote_version:
        print("\nУже актуально. Обновление не требуется.")
        return

    print(f"\nДоступно обновление: {local_version_str} -> {remote_version_str}")

    # 4. Проверка совместимости Python
    requires_python = _parse_requires_python(remote_toml)
    if requires_python:
        if not _check_python_compatibility(requires_python):
            print(
                f"\nВНИМАНИЕ: версия {remote_version_str} требует "
                f"Python {requires_python}."
            )
            print(f"Ваша версия: Python {sys.version_info.major}.{sys.version_info.minor}")
            answer = input("Продолжить обновление? (yes/no): ").strip().lower()
            if answer not in ("yes", "y", "да", "д"):
                print("Обновление отменено.")
                return

    # 5. Поиск pip
    pip_cmd = _find_pip()
    if pip_cmd is None:
        print("Ошибка: не удалось найти pip.")
        print("Установите pip: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)

    if pip_cmd == sys.executable:
        pip_args = [pip_cmd, "-m", "pip"]
    else:
        pip_args = [pip_cmd]

    # 6. Обновление
    print(f"\nВыполняется обновление...")
    install_url = f"git+{REPO_URL}.git"
    cmd = pip_args + ["install", "--upgrade", install_url]

    try:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode == 0:
            print(f"\nОбновление завершено: {local_version_str} -> {remote_version_str}")
        else:
            print(f"\nОшибка: pip завершился с кодом {result.returncode}")
            sys.exit(1)
    except Exception as e:
        print(f"Ошибка при обновлении: {e}")
        sys.exit(1)
