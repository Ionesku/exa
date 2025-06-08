#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - Скрипт запуска
Удобный способ запуска приложения с проверками
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    return True


def check_tkinter():
    """Проверка доступности tkinter"""
    try:
        import tkinter
        return True
    except ImportError:
        print("❌ tkinter не установлен")
        print("   Установите tkinter: sudo apt-get install python3-tk (Linux)")
        return False


def check_modules():
    """Проверка доступности модулей"""
    try:
        # Проверяем, что мы можем импортировать наши модули
        from modules import Task, DatabaseManager
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        print("   Убедитесь, что все файлы находятся в правильных папках")
        return False


def setup_environment():
    """Настройка окружения"""
    # Добавляем текущую папку в путь
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))


def main():
    """Основная функция запуска"""
    print("🚀 Запуск Task Manager...")

    # Проверки
    if not check_python_version():
        return 1

    if not check_tkinter():
        return 1

    setup_environment()

    if not check_modules():
        return 1

    print("✅ Все проверки пройдены")
    print("📋 Загрузка приложения...")

    try:
        # Импортируем и запускаем основное приложение
        from run import main as run_app
        run_app()
        return 0

    except KeyboardInterrupt:
        print("\n👋 Завершение работы по запросу пользователя")
        return 0

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())