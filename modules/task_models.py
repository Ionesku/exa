# -*- coding: utf-8 -*-
"""
Task Manager - Модели данных
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TaskType:
    """Тип задачи"""
    id: int = 0
    name: str = ""
    color: str = "#2196F3"
    description: str = ""


@dataclass
class Task:
    """Класс задачи"""
    id: int = 0
    title: str = ""
    content: str = ""
    importance: int = 1  # 1-10
    duration: int = 30  # минуты
    has_duration: bool = False  # есть ли установленная длительность
    priority: int = 5  # 1-10 (зеленый к красному)
    task_type_id: int = 1
    is_completed: bool = False
    quadrant: int = 0  # 0-не размещена, 1-4 квадранты
    date_created: str = ""
    date_scheduled: str = ""
    is_recurring: bool = False
    recurrence_pattern: str = ""
    move_count: int = 0  # количество перемещений между квадрантами

    def __post_init__(self):
        if not self.date_created:
            self.date_created = datetime.now().isoformat()

    @property
    def is_planned(self) -> bool:
        """Запланирована ли задача (перемещена в квадрант)"""
        return self.quadrant > 0