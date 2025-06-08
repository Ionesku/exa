# -*- coding: utf-8 -*-
"""
Task Manager - Модули
"""

from modules.task_models import Task, TaskType
from modules.database import DatabaseManager
from modules.colors import get_priority_color, QUADRANT_COLORS, UI_COLORS
from modules.ui_components import (
    FullScreenQuadrantsWidget,
    CompactTaskListWidget,
    TaskEditDialog,
    TaskTypeDialog
)
from modules.calendar_manager import CalendarMixin
from modules.drag_drop import DragDropMixin
from modules.utils import (
    DateUtils, DatabaseUtils, UIUtils, TaskUtils, ValidationUtils,
    safe_int, safe_float, truncate_text
)

__all__ = [
    # Модели данных
    'Task', 'TaskType',

    # Основные компоненты
    'DatabaseManager',

    # Цвета и стили
    'get_priority_color', 'QUADRANT_COLORS', 'UI_COLORS',

    # UI компоненты
    'FullScreenQuadrantsWidget', 'CompactTaskListWidget', 'TaskEditDialog', 'TaskTypeDialog',

    # Mixins
    'CalendarMixin', 'DragDropMixin',

    # Утилиты
    'DateUtils', 'DatabaseUtils', 'UIUtils', 'TaskUtils', 'ValidationUtils',
    'safe_int', 'safe_float', 'truncate_text'
]