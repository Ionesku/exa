# -*- coding: utf-8 -*-
"""
Task Manager - Утилиты и вспомогательные функции
"""

from datetime import date
from typing import Dict, List
from .task_models import Task, TaskType


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


class TaskUtils:
    """Утилиты для работы с задачами"""

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

        return max(0, score)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезка текста с добавлением суффикса"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix