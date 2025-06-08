# -*- coding: utf-8 -*-
"""
Task Manager - Конфигурация приложения
"""

from pathlib import Path

# Пути к файлам
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "tasks.db"
BACKUP_DIR = BASE_DIR / "backups"

# Настройки интерфейса
UI_CONFIG = {
    # Основное окно
    'window_width': 1000,
    'window_height': 700,
    'window_title': 'Task Manager',

    # Квадранты планирования
    'quadrant_size': 140,
    'max_tasks_per_quadrant': 4,

    # Список задач
    'task_list_width': 300,

    # Шрифты
    'default_font': ('Arial', 10),
    'header_font': ('Arial', 12, 'bold'),
    'small_font': ('Arial', 8),

    # Отступы
    'padding': 5,
    'margin': 10,
}

# Настройки цветов
COLOR_CONFIG = {
    # Пастельные настройки
    'pastel_saturation': 0.25,
    'pastel_lightness': 0.9,

    # Базовые оттенки для квадрантов
    'quadrant_hues': {
        1: 120,  # Зеленый
        2: 210,  # Голубой
        3: 30,  # Оранжевый
        4: 270,  # Фиолетовый
    },

    # Системные цвета
    'primary': '#2196F3',
    'accent': '#FF5722',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    'background': '#FFFFFF',
    'text_primary': '#212121',
    'text_secondary': '#757575',
    'border': '#E0E0E0',
    'inactive': '#F8F8F8',
}

# Настройки базы данных
DATABASE_CONFIG = {
    'path': str(DATABASE_PATH),
    'backup_enabled': True,
    'backup_interval_days': 7,
    'auto_vacuum': True,
    'journal_mode': 'WAL',  # Write-Ahead Logging для лучшей производительности
}

# Настройки поведения
BEHAVIOR_CONFIG = {
    # Автосохранение
    'auto_save_interval': 30,  # секунды
    'auto_backup_enabled': True,

    # Drag & Drop
    'drag_sensitivity': 5,  # пикселей
    'drop_highlight_color': '#E0E0E0',

    # Уведомления
    'show_notifications': True,
    'notification_duration': 3000,  # миллисекунды

    # Производительность
    'max_undo_levels': 10,
    'lazy_loading': True,
}

# Настройки времени
TIME_CONFIG = {
    # Рабочий день
    'default_start_hour': 9,
    'default_end_hour': 21,
    'break_duration': 15,  # минуты

    # Форматы
    'date_format': '%d.%m.%Y',
    'time_format': '%H:%M',
    'datetime_format': '%d.%m.%Y %H:%M',

    # Локализация
    'locale': 'ru_RU',
    'first_day_of_week': 0,  # 0 = Понедельник
}

# Горячие клавиши
HOTKEYS_CONFIG = {
    'new_task': '<Control-n>',
    'save_task': '<Control-s>',
    'delete_task': '<Control-d>',
    'show_calendar': '<Control-k>',
    'show_backlog': '<Control-b>',
    'toggle_edit': '<Control-e>',
    'help': '<F1>',
    'quit': '<Control-q>',
}

# Настройки разработки
DEBUG_CONFIG = {
    'debug_mode': False,
    'log_level': 'INFO',
    'log_file': str(BASE_DIR / 'task_manager.log'),
    'profile_performance': False,
    'show_fps_counter': False,
}

# Экспериментальные функции
EXPERIMENTAL_CONFIG = {
    'enable_themes': False,
    'enable_plugins': False,
    'enable_sync': False,
    'enable_ai_suggestions': False,
}


# Функции для работы с конфигурацией
def get_ui_config(key: str, default=None):
    """Получить настройку интерфейса"""
    return UI_CONFIG.get(key, default)


def get_color_config(key: str, default=None):
    """Получить настройку цвета"""
    return COLOR_CONFIG.get(key, default)


def get_database_config(key: str, default=None):
    """Получить настройку базы данных"""
    return DATABASE_CONFIG.get(key, default)


def is_debug_enabled() -> bool:
    """Проверить, включен ли режим отладки"""
    return DEBUG_CONFIG.get('debug_mode', False)


def is_feature_enabled(feature: str) -> bool:
    """Проверить, включена ли экспериментальная функция"""
    return EXPERIMENTAL_CONFIG.get(feature, False)


# Валидация конфигурации
def validate_config():
    """Проверка корректности конфигурации"""
    errors = []

    # Проверка размеров окна
    if UI_CONFIG['window_width'] < 800:
        errors.append("Ширина окна слишком мала (минимум 800px)")

    if UI_CONFIG['window_height'] < 600:
        errors.append("Высота окна слишком мала (минимум 600px)")

    # Проверка квадрантов
    if UI_CONFIG['quadrant_size'] < 100:
        errors.append("Размер квадранта слишком мал")

    # Проверка путей
    if not BASE_DIR.exists():
        errors.append(f"Базовая директория не существует: {BASE_DIR}")

    return errors


# Автопроверка при импорте
if __name__ != "__main__":
    config_errors = validate_config()
    if config_errors:
        print("⚠️  Ошибки конфигурации:")
        for error in config_errors:
            print(f"   • {error}")