# -*- coding: utf-8 -*-
"""
Task Manager - Модуль для реализации Drag & Drop функциональности
"""

import tkinter as tk
from typing import Optional, Callable, Any


class DragDropManager:
    """Менеджер для работы с перетаскиванием"""

    def __init__(self):
        self.dragged_widget: Optional[tk.Widget] = None
        self.dragged_data: Optional[Any] = None
        self.drag_start_x: int = 0
        self.drag_start_y: int = 0
        self.drop_zones: dict = {}
        self.drag_ghost: Optional[tk.Toplevel] = None

    def make_draggable(self, widget: tk.Widget, data: Any = None,
                       drag_start_callback: Optional[Callable] = None):
        """Сделать виджет перетаскиваемым"""

        def on_drag_start(event):
            self.dragged_widget = widget
            self.dragged_data = data
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root

            if drag_start_callback:
                drag_start_callback(event, data)

            # Создание призрачного изображения
            self.create_drag_ghost(widget, event.x_root, event.y_root)

            widget.bind('<B1-Motion>', on_drag_motion)
            widget.bind('<ButtonRelease-1>', on_drag_end)

        def on_drag_motion(event):
            if self.drag_ghost:
                self.drag_ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        def on_drag_end(event):
            # Определение зоны сброса
            drop_zone = self.find_drop_zone(event.x_root, event.y_root)

            if drop_zone and 'callback' in self.drop_zones[drop_zone]:
                self.drop_zones[drop_zone]['callback'](self.dragged_data, drop_zone)

            self.cleanup_drag()
            if widget.winfo_exists():
                widget.unbind('<B1-Motion>')
                widget.unbind('<ButtonRelease-1>')

        widget.bind('<Button-1>', on_drag_start)

    def register_drop_zone(self, zone_id: str, widget: tk.Widget,
                           callback: Callable, highlight_color: str = None):
        """Регистрация зоны для сброса"""
        self.drop_zones[zone_id] = {
            'widget': widget,
            'callback': callback,
            'highlight_color': highlight_color,
            'original_bg': widget.cget('bg') if hasattr(widget, 'cget') else None
        }

        # Добавление визуальной обратной связи
        def on_enter(event):
            if self.dragged_widget and highlight_color:
                try:
                    widget.config(bg=highlight_color)
                except:
                    pass

        def on_leave(event):
            if self.dragged_widget and self.drop_zones[zone_id]['original_bg']:
                try:
                    widget.config(bg=self.drop_zones[zone_id]['original_bg'])
                except:
                    pass

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def create_drag_ghost(self, widget: tk.Widget, x: int, y: int):
        """Создание призрачного изображения при перетаскивании"""
        self.drag_ghost = tk.Toplevel()
        self.drag_ghost.wm_overrideredirect(True)
        self.drag_ghost.wm_attributes('-alpha', 0.7)
        self.drag_ghost.geometry(f"+{x + 10}+{y + 10}")

        # Создание упрощенной копии виджета
        if hasattr(widget, 'cget'):
            try:
                text = widget.cget('text')
                label = tk.Label(self.drag_ghost, text=text,
                                 bg='lightgray', relief='solid', bd=1)
                label.pack()
            except:
                # Если не удается получить текст, показываем простую метку
                label = tk.Label(self.drag_ghost, text="●",
                                 bg='lightgray', relief='solid', bd=1)
                label.pack()

    def find_drop_zone(self, x: int, y: int) -> Optional[str]:
        """Поиск зоны сброса по координатам"""
        for zone_id, zone_data in self.drop_zones.items():
            widget = zone_data['widget']

            # Получение координат виджета
            try:
                widget_x = widget.winfo_rootx()
                widget_y = widget.winfo_rooty()
                widget_w = widget.winfo_width()
                widget_h = widget.winfo_height()

                if (widget_x <= x <= widget_x + widget_w and
                        widget_y <= y <= widget_y + widget_h):
                    return zone_id
            except:
                continue

        return None

    def cleanup_drag(self):
        """Очистка после завершения перетаскивания"""
        if self.drag_ghost:
            self.drag_ghost.destroy()
            self.drag_ghost = None

        # Восстановление оригинальных цветов
        for zone_data in self.drop_zones.values():
            if zone_data['original_bg']:
                try:
                    zone_data['widget'].config(bg=zone_data['original_bg'])
                except:
                    pass

        self.dragged_widget = None
        self.dragged_data = None


class TaskDragDropMixin:
    """Миксин для добавления drag&drop функциональности к TaskManager"""

    def init_drag_drop(self):
        """Инициализация drag&drop"""
        self.drag_manager = DragDropManager()
        self.setup_drop_zones()

    def setup_drop_zones(self):
        """Настройка зон для сброса задач"""
        # Регистрация квадрантов как зон сброса
        for quad_id in range(1, 5):
            if quad_id in self.quadrants:
                self.drag_manager.register_drop_zone(
                    f'quadrant_{quad_id}',
                    self.quadrants[quad_id]['task_area'],
                    lambda task, zone, q=quad_id: self.drop_task_to_quadrant(task, q),
                    '#E0E0E0'  # Цвет подсветки при наведении
                )

        # Регистрация области переработок
        if hasattr(self, 'overtime_area'):
            self.drag_manager.register_drop_zone(
                'overtime',
                self.overtime_area,
                lambda task, zone: self.drop_task_to_overtime(task),
                '#FFECB3'
            )

    def make_task_draggable(self, widget: tk.Widget, task):
        """Сделать задачу перетаскиваемой"""
        self.drag_manager.make_draggable(
            widget,
            task,
            lambda event, task_data: self.on_task_drag_start(event, task_data)
        )

    def on_task_drag_start(self, event, task):
        """Обработка начала перетаскивания задачи"""
        # Можно добавить дополнительную логику при начале перетаскивания
        pass

    def drop_task_to_quadrant(self, task, quadrant: int):
        """Сброс задачи в квадрант"""
        if not task:
            return

        # Увеличиваем счетчик перемещений
        old_quadrant = task.quadrant
        task.quadrant = quadrant

        if old_quadrant != quadrant:
            task.move_count += 1
            # Увеличиваем важность при каждом перемещении
            task.importance = min(10, task.importance + 1)

        # Сохранение изменений
        self.db.save_task(task)

        # Обновление интерфейса
        self.refresh_task_list()

        # Если это текущая задача, обновляем редактор
        if self.current_task and self.current_task.id == task.id:
            self.current_task = task
            self.load_task_to_editor(task)

    def drop_task_to_overtime(self, task):
        """Сброс задачи в область переработок"""
        if not task:
            return

        # Помечаем задачу как относящуюся к переработкам
        # Можно добавить специальное поле или использовать существующие
        task.quadrant = 5  # Специальное значение для переработок
        task.move_count += 1

        # Сохранение изменений
        self.db.save_task(task)

        # Обновление интерфейса
        self.refresh_task_list()


# Пример интеграции с основным классом TaskManager
"""
Чтобы интегрировать drag&drop в основной класс TaskManager, 
нужно добавить наследование от TaskDragDropMixin:

class TaskManager(TaskDragDropMixin):
    def __init__(self):
        # ... существующий код инициализации ...

        # Инициализация drag&drop после создания интерфейса
        self.init_drag_drop()

    def create_task_button(self, task):
        # ... существующий код создания кнопки ...

        # Добавление drag&drop к кнопке задачи
        self.make_task_draggable(task_btn, task)

    def add_task_to_quadrant(self, task, quadrant):
        # ... существующий код добавления в квадрант ...

        # Добавление drag&drop к индикатору в квадранте
        self.make_task_draggable(task_circle, task)
"""