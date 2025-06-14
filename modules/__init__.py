# -*- coding: utf-8 -*-
"""
Task Manager - Модули
"""

from modules.task_models import Task, TaskType
from modules.database import DatabaseManager
from modules.colors import get_priority_color, QUADRANT_COLORS, UI_COLORS
from modules.quadrants_widget import QuadrantsWidget
from modules.task_list_widget import TaskListWidget
from modules.task_detail_panel import TaskDetailPanel
from modules.task_edit_dialog import TaskEditDialog
from modules.task_type_dialog import TaskTypeDialog
from modules.calendar_window import CalendarWindow
from modules.utils import DateUtils, TaskUtils, truncate_text

__all__ = [
    # Модели данных
    'Task', 'TaskType',

    # База данных
    'DatabaseManager',

    # Цвета
    'get_priority_color', 'QUADRANT_COLORS', 'UI_COLORS',

    # UI компоненты
    'QuadrantsWidget', 'TaskListWidget', 'TaskDetailPanel',
    'TaskEditDialog', 'TaskTypeDialog', 'CalendarWindow',

    # Утилиты
    'DateUtils', 'TaskUtils', 'truncate_text'
]