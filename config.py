# -*- coding: utf-8 -*-
"""
Task Manager - Конфигурация приложения (обновленная версия)
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
    'responsive_threshold': 900,  # Ширина для переключения на вертикальную компоновку

    # Квадранты планирования (полноэкранные)
    'quadrant_border_width': 2,
    'quadrant_padding': 25,
    'max_tasks_per_quadrant': 5,  # "Не влезает - не влезает!"

    # Список задач (компактный)
    'task_list_width': 250,
    'task_block_height': 40,
    'task_title_max_length': 20,

    # Диалоги
    'dialog_width': 500,
    'dialog_height': 600,
    'task_type_dialog_width': 350,
    'task_type_dialog_height': 250,

    # Шрифты
    'default_font': ('Arial', 10),
    'header_font': ('Arial', 12, 'bold'),
    'small_font': ('Arial', 8),
    'bold_font': ('Arial', 10, 'bold'),
    'time_font': ('Arial', 10, 'bold'),

    # Отступы
    'padding': 5,
    'margin': 10,
}

# Настройки цветов (пастельные, вычисляемые)
COLOR_CONFIG = {
    # Пастельные настройки для квадрантов
    'pastel_saturation': 0.25,
    'pastel_lightness': 0.9,

    # Базовые оттенки для квадрантов (HSL)
    'quadrant_hues': {
        1: 120,  # Зеленый (12:00-15:00)
        2: 210,  # Голубой (15:00-18:00)
        3: 30,  # Оранжевый (18:00-21:00)
        4: 270,  # Фиолетовый (09:00-12:00)
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

    # Цвета для drag & drop
    'drop_highlight': '#D0D0D0',
    'drag_ghost_alpha': 0.7,
    'selected_task_factor': 0.7,  # Для затемнения выбранных задач
}

# Настройки базы данных
DATABASE_CONFIG = {
    'path': str(DATABASE_PATH),
    'backup_enabled': True,
    'backup_interval_days': 7,
    'auto_vacuum': True,
    'journal_mode': 'WAL',
    'max_backup_files': 10,
}

# Настройки поведения
BEHAVIOR_CONFIG = {
    # Автосохранение
    'auto_save_interval': 30,  # секунды
    'auto_backup_enabled': True,
    'save_last_location': True,  # Сохранять последнее место сохранения

    # Drag & Drop
    'drag_sensitivity': 5,
    'enable_drag_ghost': True,
    'drag_visual_feedback': True,

    # Задачи
    'default_task_duration': 30,  # минуты
    'max_task_title_display': 17,  # символов
    'auto_increase_importance': True,  # При перемещении между квадрантами

    # Уведомления
    'show_notifications': True,
    'notification_duration': 3000,

    # Календарь
    'calendar_optimization': True,  # Оптимизация перерисовки
    'show_task_count_in_calendar': True,

    # Производительность
    'max_undo_levels': 10,
    'lazy_loading': True,
}

# Настройки времени
TIME_CONFIG = {
    # Рабочий день
    'default_start_hour': 9,
    'work_duration_hours': 12,  # 9:00 + 12 = 21:00
    'quadrant_duration_hours': 3,  # Каждый квадрант = 3 часа

    # Редактирование времени
    'allow_time_editing': True,  # Клик по времени для редактирования
    'time_format_24h': True,

    # Форматы
    'date_format': '%d.%m.%Y',
    'time_format': '%H:%M',
    'datetime_format': '%d.%m.%Y %H:%M',
    'display_time_format': '%H:%M',

    # Локализация
    'locale': 'ru_RU',
    'first_day_of_week': 0,  # 0 = Понедельник
    'weekday_names': [
        'Понедельник', 'Вторник', 'Среда', 'Четверг',
        'Пятница', 'Суббота', 'Воскресенье'
    ],
    'month_names': [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]
}

# Горячие клавиши (обновленные)
HOTKEYS_CONFIG = {
    'new_task': '<Control-n>',
    'quick_save': '<Control-s>',  # Переименовано с save_task
    'delete_task': '<Control-d>',
    'edit_task': '<Control-e>',
    'show_calendar': '<Control-k>',
    'show_backlog': '<Control-b>',
    'help': '<F1>',
    'quit': '<Control-q>',
    'start_day': '<F2>',
    'end_day': '<F3>',
}

# Настройки бэклога
BACKLOG_CONFIG = {
    'group_by_type': True,  # Группировка по типам задач
    'show_extended_info': True,  # Показывать важность, срочность, длительность
    'enable_type_tabs': True,  # Вкладки для типов
    'max_title_length': 50,  # Максимальная длина названия в бэклоге
}

# Настройки разработки
DEBUG_CONFIG = {
    'debug_mode': False,
    'log_level': 'INFO',
    'log_file': str(BASE_DIR / 'task_manager.log'),
    'profile_performance': False,
    'show_drag_debug': False,  # Отладка drag & drop
    'test_mode': False,
}

# Экспериментальные функции
EXPERIMENTAL_CONFIG = {
    'enable_themes': False,
    'enable_plugins': False,
    'enable_sync': False,
    'enable_ai_suggestions': False,
    'enable_advanced_analytics': False,
    'enable_voice_input': False,
}

# Настройки компонентов
COMPONENT_CONFIG = {
    # Квадранты
    'quadrants': {
        'enable_scrolling': False,  # НЕТ прокрутки в квадрантах!
        'strict_task_limit': True,  # Строгий лимит задач
        'show_time_inside': True,  # Время внутри квадрантов
        'editable_time': True,  # Время редактируется кликом
        'unified_block': True,  # Единый блок времени
    },

    # Список задач
    'task_list': {
        'compact_mode': True,  # Компактный режим
        'no_buttons': True,  # Без кнопок
        'no_checkboxes': True,  # Без чекбоксов
        'color_background': True,  # Цвет фона по приоритету
        'show_planning_indicator': True,  # Индикатор планирования 📅
    },

    # Редактирование задач
    'task_editor': {
        'popup_mode': True,  # Всплывающий диалог
        'remember_location': True,  # Запоминать место сохранения
        'priority_to_urgency': True,  # "Приоритет" -> "Срочность"
        'optional_duration': True,  # Длительность опциональна
    }
}


# Функции для работы с конфигурацией
def get_ui_config(key: str, default=None):
    """Получить настройку интерфейса"""
    return UI_CONFIG.get(key, default)


def get_color_config(key: str, default=None):
    """Получить настройку цвета"""
    return COLOR_CONFIG.get(key, default)


def get_behavior_config(key: str, default=None):
    """Получить настройку поведения"""
    return BEHAVIOR_CONFIG.get(key, default)


def get_component_config(component: str, key: str = None, default=None):
    """Получить настройку компонента"""
    if component not in COMPONENT_CONFIG:
        return default

    if key is None:
        return COMPONENT_CONFIG[component]

    return COMPONENT_CONFIG[component].get(key, default)


def is_debug_enabled() -> bool:
    """Проверить, включен ли режим отладки"""
    return DEBUG_CONFIG.get('debug_mode', False)


def is_feature_enabled(feature: str) -> bool:
    """Проверить, включена ли экспериментальная функция"""
    return EXPERIMENTAL_CONFIG.get(feature, False)


def get_responsive_threshold() -> int:
    """Получить порог для responsive дизайна"""
    return UI_CONFIG.get('responsive_threshold', 900)


def get_quadrant_hue(quadrant_id: int) -> int:
    """Получить оттенок для квадранта"""
    return COLOR_CONFIG['quadrant_hues'].get(quadrant_id, 120)


def get_max_tasks_per_quadrant() -> int:
    """Получить максимальное количество задач в квадранте"""
    return UI_CONFIG.get('max_tasks_per_quadrant', 5)


# Валидация конфигурации (обновленная)
def validate_config():
    """Проверка корректности конфигурации"""
    errors = []

    # Проверка размеров окна
    if UI_CONFIG['window_width'] < 800:
        errors.append("Ширина окна слишком мала (минимум 800px)")

    if UI_CONFIG['window_height'] < 600:
        errors.append("Высота окна слишком мала (минимум 600px)")

    # Проверка responsive порога
    if UI_CONFIG['responsive_threshold'] < 700:
        errors.append("Порог responsive слишком мал")

    # Проверка настроек квадрантов
    if UI_CONFIG['max_tasks_per_quadrant'] < 1:
        errors.append("Максимум задач в квадранте должен быть >= 1")

    if UI_CONFIG['max_tasks_per_quadrant'] > 10:
        errors.append("Слишком много задач в квадранте (рекомендуется <= 5)")

    # Проверка цветовых настроек
    if not all(0 <= hue <= 360 for hue in COLOR_CONFIG['quadrant_hues'].values()):
        errors.append("Неверные значения оттенков для квадрантов (0-360)")

    # Проверка путей
    if not BASE_DIR.exists():
        errors.append(f"Базовая директория не существует: {BASE_DIR}")

    return errors


# Конфигурация по умолчанию для новых пользователей
DEFAULT_USER_CONFIG = {
    'first_run': True,
    'tutorial_completed': False,
    'preferred_start_hour': 9,
    'preferred_layout': 'horizontal',
    'show_tips': True,
    'enable_sounds': False,
}

# Автопроверка при импорте
if __name__ != "__main__":
    config_errors = validate_config()
    if config_errors and is_debug_enabled():
        print("⚠️  Ошибки конфигурации:")
        for error in config_errors:
            print(f"   • {error}")