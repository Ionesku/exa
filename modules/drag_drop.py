# -*- coding: utf-8 -*-
"""
Task Manager - Модуль для реализации Drag & Drop функциональности (обновленный)
"""

import tkinter as tk
from typing import Optional
from .task_models import Task


class DragDropMixin:
    """Миксин для добавления drag&drop функциональности"""

    def init_drag_drop(self):
        """Инициализация drag&drop"""
        self.dragged_task: Optional[Task] = None
        self.drag_widget: Optional[tk.Widget] = None
        self.drag_ghost: Optional[tk.Toplevel] = None

    def make_task_draggable(self, widget: tk.Widget, task: Task):
        """Сделать задачу перетаскиваемой (базовый метод)"""

        def start_drag(event):
            self.dragged_task = task
            self.drag_widget = widget
            self.select_task(task)

        widget.bind('<Button-1>', start_drag)

    def start_drag_from_list(self, task: Task):
        """Начало перетаскивания из списка задач"""
        self.dragged_task = task
        print(f"Перетаскивание задачи из списка: {task.title}")

        # Создаем призрачное изображение
        self.create_drag_ghost(task)

    def start_drag_from_quadrant(self, task: Task):
        """Начало перетаскивания из квадранта"""
        self.dragged_task = task
        print(f"Перетаскивание задачи из квадранта: {task.title}")

        # Создаем призрачное изображение
        self.create_drag_ghost(task)

    def start_drag_from_backlog(self, task: Task):
        """Начало перетаскивания из бэклога"""
        self.dragged_task = task
        print(f"Перетаскивание задачи из бэклога: {task.title}")

        self.create_drag_ghost(task)


    def create_drag_ghost(self, task: Task):
        """Создание призрачного изображения при перетаскивании"""
        if self.drag_ghost:
            self.drag_ghost.destroy()

        self.drag_ghost = tk.Toplevel(self.root)
        self.drag_ghost.wm_overrideredirect(True)
        self.drag_ghost.wm_attributes('-alpha', 0.7)
        self.drag_ghost.wm_attributes('-topmost', True)

        # Создаем визуальное представление задачи
        from .colors import get_priority_color

        label = tk.Label(self.drag_ghost,
                         text=task.title[:15] + ("..." if len(task.title) > 15 else ""),
                         bg=get_priority_color(task.priority),
                         fg='white',
                         font=('Arial', 9, 'bold'),
                         relief='solid',
                         bd=2,
                         padx=5,
                         pady=2)
        label.pack()

        # Позиционируем призрак
        x, y = self.root.winfo_pointerxy()
        self.drag_ghost.geometry(f"+{x + 10}+{y + 10}")

        # Привязываем движение мыши
        self.root.bind('<Motion>', self.on_drag_motion)
        self.root.bind('<ButtonRelease-1>', self.on_drag_end)

    def on_drag_motion(self, event):
        """Обработка движения мыши при перетаскивании"""
        if self.drag_ghost:
            x = event.x_root + 10
            y = event.y_root + 10
            self.drag_ghost.geometry(f"+{x}+{y}")

    def on_drag_end(self, event):
        """Завершение перетаскивания"""
        # Удаляем призрак
        if self.drag_ghost:
            self.drag_ghost.destroy()
            self.drag_ghost = None

        # Снимаем привязки
        self.root.unbind('<Motion>')
        self.root.unbind('<ButtonRelease-1>')

        # Очищаем перетаскиваемую задачу
        self.dragged_task = None
        self.drag_widget = None

    def move_task_to_quadrant(self, task: Task, quadrant: int):
        """Перемещение задачи в квадрант"""
        print(f"Перемещение задачи '{task.title}' в квадрант {quadrant}")

        old_quadrant = task.quadrant
        task.quadrant = quadrant

        if not task.date_scheduled:
            task.date_scheduled = self.current_date.isoformat()

        if old_quadrant != quadrant:
            task.move_count += 1
            task.importance = min(10, task.importance + 1)

        self.db.save_task(task)
        self.refresh_task_list()

        if self.current_task and self.current_task.id == task.id:
            self.current_task = task

        # Очищаем drag state
        self.cleanup_drag()

    def move_task_to_overtime(self, task: Task):
        """Перемещение задачи в область переработок"""
        task.quadrant = 5
        task.move_count += 1

        self.db.save_task(task)
        self.refresh_task_list()

        # Очищаем drag state
        self.cleanup_drag()

    def move_task_from_backlog(self, task: Task):
        """Перемещение задачи из бэклога в текущий день"""
        print(f"Перемещение задачи из бэклога: {task.title}")

        # Устанавливаем дату на сегодня
        task.date_scheduled = self.current_date.isoformat()
        task.quadrant = 0  # Сбрасываем квадрант

        self.db.save_task(task)
        self.refresh_task_list()

        # Очищаем drag state
        self.cleanup_drag()

    def move_task_to_backlog(self, task: Task):
        """Перемещение задачи из сегодняшнего дня в бэклог"""
        print(f"Перемещение задачи в бэклог: {task.title}")

        task.date_scheduled = ""
        task.quadrant = 0

        self.db.save_task(task)
        self.refresh_task_list()

        self.cleanup_drag()


    def cleanup_drag(self):
        """Очистка состояния перетаскивания"""
        if self.drag_ghost:
            self.drag_ghost.destroy()
            self.drag_ghost = None

        self.dragged_task = None
        self.drag_widget = None

        # Снимаем привязки если есть
        try:
            self.root.unbind('<Motion>')
            self.root.unbind('<ButtonRelease-1>')
        except:
            pass