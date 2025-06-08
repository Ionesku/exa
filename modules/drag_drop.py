# -*- coding: utf-8 -*-
"""
Task Manager - Модуль для реализации Drag & Drop функциональности
"""

import tkinter as tk
from typing import Optional, Any
from modules.task_models import Task


class DragDropMixin:
    """Миксин для добавления drag&drop функциональности"""

    def init_drag_drop(self):
        """Инициализация drag&drop"""
        self.dragged_task: Optional[Task] = None

    def make_task_draggable(self, widget: tk.Widget, task: Task):
        """Сделать задачу перетаскиваемой"""

        def start_drag(event):
            self.dragged_task = task
            self.select_task(task)

            # Визуальная обратная связь
            original_relief = widget.cget('relief')
            widget.config(relief='sunken')
            widget.after(100, lambda: widget.config(relief=original_relief))

        widget.bind('<Button-1>', start_drag)

    def move_task_to_quadrant(self, task: Task, quadrant: int):
        """Перемещение задачи в квадрант"""
        old_quadrant = task.quadrant
        task.quadrant = quadrant

        if old_quadrant != quadrant:
            task.move_count += 1
            task.importance = min(10, task.importance + 1)

        self.db.save_task(task)
        self.refresh_task_list()

        if self.current_task and self.current_task.id == task.id:
            self.current_task = task
            self.load_task_to_editor(task)

        # Очищаем перетаскиваемую задачу
        self.dragged_task = None

    def move_task_to_overtime(self, task: Task):
        """Перемещение задачи в область переработок"""
        task.quadrant = 5
        task.move_count += 1

        self.db.save_task(task)
        self.refresh_task_list()

        # Очищаем перетаскиваемую задачу
        self.dragged_task = None