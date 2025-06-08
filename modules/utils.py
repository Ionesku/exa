# -*- coding: utf-8 -*-
"""
Task Manager - Утилиты и вспомогательные функции
"""

import json
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import sqlite3
import tkinter as tk
from tkinter import messagebox

from modules.task_models import Task, TaskType


class DateUtils:
    """Утилиты для работы с датами"""

    @staticmethod
    def format_date_russian(date_obj: date) -> str:
        """Форматирование даты на русском языке"""
        month_names = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ]

        day = date_obj.day
        month = month_names[date_obj.month - 1]
        year = date_obj.year

        return f"{day} {month} {year}"

    @staticmethod
    def get_weekday_russian(date_obj: date) -> str:
        """Получить день недели на русском языке"""
        weekdays = [
            'Понедельник', 'Вторник', 'Среда', 'Четверг',
            'Пятница', 'Суббота', 'Воскресенье'
        ]
        return weekdays[date_obj.weekday()]

    @staticmethod
    def parse_date_string(date_str: str) -> Optional[date]:
        """Парсинг строки даты в различных форматах"""
        formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%y']

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def get_week_dates(target_date: date) -> List[date]:
        """Получить все даты недели для заданной даты"""
        # Находим понедельник
        monday = target_date - timedelta(days=target_date.weekday())

        # Генерируем все дни недели
        return [monday + timedelta(days=i) for i in range(7)]


class DatabaseUtils:
    """Утилиты для работы с базой данных"""

    @staticmethod
    def backup_database(db_path: str, backup_dir: str) -> bool:
        """Создание резервной копии базы данных"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"tasks_backup_{timestamp}.db"
            backup_file = backup_path / backup_filename

            shutil.copy2(db_path, backup_file)

            # Удаляем старые бэкапы (оставляем последние 10)
            DatabaseUtils.cleanup_old_backups(backup_dir, keep_count=10)

            return True

        except Exception as e:
            print(f"Ошибка создания бэкапа: {e}")
            return False

    @staticmethod
    def cleanup_old_backups(backup_dir: str, keep_count: int = 10):
        """Удаление старых резервных копий"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return

            # Получаем все файлы бэкапов
            backup_files = list(backup_path.glob("tasks_backup_*.db"))

            # Сортируем по времени создания
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Удаляем лишние
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()

        except Exception as e:
            print(f"Ошибка очистки бэкапов: {e}")

    @staticmethod
    def export_tasks_to_json(db_path: str, output_file: str) -> bool:
        """Экспорт задач в JSON"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Получаем все задачи
            cursor.execute('SELECT * FROM tasks')
            tasks_data = cursor.fetchall()

            # Получаем типы задач
            cursor.execute('SELECT * FROM task_types')
            types_data = cursor.fetchall()

            conn.close()

            # Формируем данные для экспорта
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'tasks': [
                    {
                        'id': row[0], 'title': row[1], 'content': row[2],
                        'importance': row[3], 'duration': row[4], 'priority': row[5],
                        'task_type_id': row[6], 'is_completed': bool(row[7]),
                        'quadrant': row[8], 'date_created': row[9],
                        'date_scheduled': row[10], 'is_recurring': bool(row[11]),
                        'recurrence_pattern': row[12], 'move_count': row[13]
                    }
                    for row in tasks_data
                ],
                'task_types': [
                    {
                        'id': row[0], 'name': row[1],
                        'color': row[2], 'description': row[3]
                    }
                    for row in types_data
                ]
            }

            # Сохраняем в файл
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            return False


class UIUtils:
    """Утилиты для интерфейса"""

    @staticmethod
    def center_window(window: tk.Toplevel, width: int, height: int):
        """Центрирование окна на экране"""
        window.update_idletasks()

        # Получаем размеры экрана
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Вычисляем позицию
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def create_tooltip(widget: tk.Widget, text: str, delay: int = 500):
        """Создание всплывающей подсказки с задержкой"""

        def on_enter(event):
            def show_tooltip():
                if hasattr(widget, '_tooltip_scheduled'):
                    tooltip = tk.Toplevel()
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

                    label = tk.Label(tooltip, text=text, background="lightyellow",
                                     relief="solid", borderwidth=1, font=('Arial', 9))
                    label.pack()

                    widget._tooltip = tooltip
                    del widget._tooltip_scheduled

            widget._tooltip_scheduled = widget.after(delay, show_tooltip)

        def on_leave(event):
            # Отменяем показ подсказки
            if hasattr(widget, '_tooltip_scheduled'):
                widget.after_cancel(widget._tooltip_scheduled)
                del widget._tooltip_scheduled

            # Скрываем подсказку
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    @staticmethod
    def show_message(title: str, message: str, message_type: str = "info"):
        """Показать сообщение с иконкой"""
        if message_type == "info":
            messagebox.showinfo(title, message)
        elif message_type == "warning":
            messagebox.showwarning(title, message)
        elif message_type == "error":
            messagebox.showerror(title, message)
        elif message_type == "question":
            return messagebox.askyesno(title, message)

    @staticmethod
    def safe_destroy_widget(widget: tk.Widget):
        """Безопасное удаление виджета"""
        try:
            if widget and widget.winfo_exists():
                widget.destroy()
        except tk.TclError:
            pass  # Виджет уже удален


class TaskUtils:
    """Утилиты для работы с задачами"""

    @staticmethod
    def calculate_task_priority_score(task: Task) -> float:
        """Вычисление общего счета приоритета задачи"""
        # Базовый приоритет
        score = task.priority * 10

        # Бонус за важность
        score += task.importance * 5

        # Штраф за количество перемещений
        score -= task.move_count * 2

        # Бонус за установленную длительность
        if task.has_duration:
            score += 5

        return max(0, score)  # Не может быть отрицательным

    @staticmethod
    def estimate_task_duration(task: Task) -> int:
        """Оценка длительности задачи на основе содержимого"""
        if task.has_duration:
            return task.duration

        # Простая эвристика на основе длины текста
        content_length = len(task.title) + len(task.content)

        if content_length < 50:
            return 15  # Короткая задача
        elif content_length < 200:
            return 30  # Средняя задача
        else:
            return 60  # Длинная задача

    @staticmethod
    def suggest_quadrant(task: Task, current_time: datetime = None) -> int:
        """Предложение квадранта для задачи"""
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour
        priority_score = TaskUtils.calculate_task_priority_score(task)

        # Логика размещения по времени и приоритету
        if 9 <= hour < 12:  # Утро
            return 4 if priority_score > 50 else 1
        elif 12 <= hour < 15:  # День
            return 1 if priority_score > 50 else 2
        elif 15 <= hour < 18:  # Вечер
            return 2 if priority_score > 50 else 3
        else:  # Поздно/рано
            return 3

    @staticmethod
    def group_tasks_by_type(tasks: List[Task], task_types: List[TaskType]) -> Dict[str, List[Task]]:
        """Группировка задач по типам"""
        type_map = {t.id: t.name for t in task_types}
        groups = {}

        for task in tasks:
            type_name = type_map.get(task.task_type_id, "Без типа")
            if type_name not in groups:
                groups[type_name] = []
            groups[type_name].append(task)

        return groups


class ValidationUtils:
    """Утилиты для валидации данных"""

    @staticmethod
    def validate_task(task: Task) -> List[str]:
        """Валидация задачи"""
        errors = []

        if not task.title.strip():
            errors.append("Название задачи не может быть пустым")

        if len(task.title) > 200:
            errors.append("Название задачи слишком длинное (максимум 200 символов)")

        if not (1 <= task.importance <= 10):
            errors.append("Важность должна быть от 1 до 10")

        if not (1 <= task.priority <= 10):
            errors.append("Приоритет должен быть от 1 до 10")

        if task.has_duration and not (5 <= task.duration <= 480):
            errors.append("Длительность должна быть от 5 до 480 минут")

        if not (0 <= task.quadrant <= 5):
            errors.append("Неверный номер квадранта")

        return errors

    @staticmethod
    def validate_task_type(task_type: TaskType) -> List[str]:
        """Валидация типа задачи"""
        errors = []

        if not task_type.name.strip():
            errors.append("Название типа не может быть пустым")

        if len(task_type.name) > 50:
            errors.append("Название типа слишком длинное (максимум 50 символов)")

        # Проверка цвета (должен быть hex)
        if not task_type.color.startswith('#') or len(task_type.color) != 7:
            errors.append("Цвет должен быть в формате #RRGGBB")

        return errors


# Глобальные утилиты
def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Безопасное преобразование в float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезка текста с добавлением суффикса"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix