# -*- coding: utf-8 -*-
"""
Task Manager - Конфигурация приложения (упрощенная версия)
"""

from pathlib import Path

# Пути к файлам
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "tasks.db"
BACKUP_DIR = BASE_DIR / "backups"

# Настройки интерфейса
UI_CONFIG = {
    # Основное окно
    'window_width': 1200,
    'window_height': 800,
    'window_title': 'Task Manager',
    'responsive_threshold': 900,  # Ширина для переключения на вертикальную компоновку

    # Квадранты планирования
    'max_tasks_per_quadrant': 12,  # Увеличено для табличного отображения
    'quadrant_grid_columns': 4,  # Максимум колонок в таблице квадранта

    # Список задач
    'task_list_width': 280,  # Увеличено для дополнительной информации
    'task_block_height': 50,  # Увеличено для двух строк
    'task_title_max_length': 30,

    # Диалоги
    'dialog_width': 500,
    'dialog_height': 450,
    'task_type_dialog_width': 350,
    'task_type_dialog_height': 250,

    # Шрифты
    'default_font': ('Arial', 10),
    'header_font': ('Arial', 12, 'bold'),
    'small_font': ('Arial', 8),
    'bold_font': ('Arial', 10, 'bold'),
}

# Настройки базы данных
DATABASE_CONFIG = {
    'path': str(DATABASE_PATH),
    'backup_enabled': True,
    'backup_interval_days': 7,
    'max_backup_files': 10,
}

# Настройки поведения
BEHAVIOR_CONFIG = {
    # Задачи
    'default_task_duration': 30,  # минуты
    'max_task_title_display': 20,  # символов
    'auto_increase_importance': True,  # При перемещении между квадрантами

    # Календарь
    'show_task_count_in_calendar': True,
}

# Настройки времени
TIME_CONFIG = {
    # Рабочий день
    'default_start_hour': 9,
    'work_duration_hours': 12,  # 9:00 + 12 = 21:00
    'quadrant_duration_hours': 3,  # Каждый квадрант = 3 часа

    # Форматы
    'date_format': '%d.%m.%Y',
    'time_format': '%H:%M',
    'datetime_format': '%d.%m.%Y %H:%M',
}

# Горячие клавиши
HOTKEYS_CONFIG = {
    'new_task': '<Control-n>',
    'quick_save': '<Control-s>',
    'delete_task': '<Control-d>',
    'help': '<F1>',
}