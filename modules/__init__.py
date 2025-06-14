# -*- coding: utf-8 -*-
"""
Task Manager - Модули
"""

# Модели данных
from modules.task_models import Task, TaskType

# База данных
from modules.database import DatabaseManager

# Система событий
from modules.event_manager import EventManager, EventType, Event

# Инкрементальные обновления
from modules.incremental_updater import IncrementalUpdater, SmartUpdateMixin, UpdateContext

# Цвета
from modules.colors import get_priority_color, get_completed_color, QUADRANT_COLORS, UI_COLORS

# UI компоненты
from modules.quadrants_widget import QuadrantsWidget
from modules.task_list_widget import TaskListWidget
from modules.task_detail_panel import TaskDetailPanel
from modules.task_edit_dialog import TaskEditDialog
from modules.task_type_dialog import TaskTypeDialog
from modules.calendar_window import CalendarWindow

# Утилиты
from modules.utils import DateUtils, TaskUtils, truncate_text

__all__ = [
    # Модели данных
    'Task', 'TaskType',

    # База данных
    'DatabaseManager',

    # Система событий
    'EventManager', 'EventType', 'Event',
    
    # Инкрементальные обновления
    'IncrementalUpdater', 'SmartUpdateMixin', 'UpdateContext',

    # Цвета
    'get_priority_color', 'get_completed_color', 'QUADRANT_COLORS', 'UI_COLORS',

    # UI компоненты
    'QuadrantsWidget', 'TaskListWidget', 'TaskDetailPanel',
    'TaskEditDialog', 'TaskTypeDialog', 'CalendarWindow',

    # Утилиты
    'DateUtils', 'TaskUtils', 'truncate_text'
]