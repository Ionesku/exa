# -*- coding: utf-8 -*-
"""
Task Manager - Компоненты интерфейса (исправлена версия с багфиксами)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import math
from typing import List, Optional, Callable, Tuple, Dict
from .task_models import Task, TaskType
from .colors import get_priority_color, QUADRANT_COLORS, UI_COLORS


class QuadrantLayoutManager:
    """Менеджер компоновки с поддержкой прямоугольников и проверкой площадей"""

    def __init__(self, quadrant_width: int = 400, quadrant_height: int = 300):
        self.quadrant_width = quadrant_width
        self.quadrant_height = quadrant_height
        self.total_area = quadrant_width * quadrant_height
        self.base_duration = 180  # 3 часа = 180 минут = 100% площади квадранта
        self.min_task_size = 35  # Минимальный размер задачи
        self.max_width_ratio = 0.8  # Максимальная ширина относительно квадранта
        self.max_height_ratio = 0.6  # Максимальная высота относительно квадранта

    def calculate_task_dimensions(self, duration: int) -> Tuple[int, int]:
        """Расчет размеров задачи - ПОДДЕРЖКА ПРЯМОУГОЛЬНИКОВ"""
        # Площадь задачи пропорциональна её длительности
        duration_ratio = min(duration / self.base_duration, 1.2)  # Разрешаем превышение на 20%
        task_area = self.total_area * duration_ratio

        # Вычисляем размеры с предпочтением эффективного заполнения
        side = math.sqrt(task_area)

        # Базовые размеры
        width = max(int(side), self.min_task_size)
        height = max(int(side), self.min_task_size)

        # НОВАЯ ЛОГИКА: адаптивные прямоугольники
        if duration <= 30:
            # Короткие задачи - компактные квадраты
            width = height = max(self.min_task_size, int(side * 0.9))
        elif duration <= 60:
            # Средние задачи - слегка вытянутые
            width = min(int(side * 1.2), int(self.quadrant_width * self.max_width_ratio))
            height = max(int(side * 0.8), self.min_task_size)
        elif duration <= 120:
            # Длинные задачи - прямоугольники
            width = min(int(side * 1.5), int(self.quadrant_width * self.max_width_ratio))
            height = max(int(side * 0.7), self.min_task_size)
        else:
            # Очень длинные задачи - широкие прямоугольники
            width = min(int(side * 2.0), int(self.quadrant_width * 0.95))
            height = max(int(side * 0.5), self.min_task_size)

        # Ограничиваем размерами квадранта
        width = min(width, self.quadrant_width - 2)
        height = min(height, self.quadrant_height - 2)

        return width, height

    def find_best_position(self, width: int, height: int,
                           occupied_positions: List[Dict]) -> Tuple[int, int]:
        """УЛУЧШЕННЫЙ алгоритм размещения БЕЗ ОТСТУПОВ"""

        # Пробуем разные стратегии размещения
        strategies = [
            self._try_top_left_fill,
            self._try_column_fill,
            self._try_row_fill,
            self._try_corner_fill
        ]

        for strategy in strategies:
            pos = strategy(width, height, occupied_positions)
            if pos:
                return pos

        # Если не нашли место, размещаем в стопку
        stack_offset = len(occupied_positions) * 2
        return stack_offset, stack_offset

    def _try_top_left_fill(self, width: int, height: int, occupied: List[Dict]) -> Optional[Tuple[int, int]]:
        """Заполнение слева направо, сверху вниз БЕЗ ОТСТУПОВ"""
        for y in range(0, self.quadrant_height - height + 1, 2):
            for x in range(0, self.quadrant_width - width + 1, 2):
                if not self._overlaps_with_existing(x, y, width, height, occupied):
                    return x, y
        return None

    def _try_column_fill(self, width: int, height: int, occupied: List[Dict]) -> Optional[Tuple[int, int]]:
        """Заполнение по колонкам"""
        for x in range(0, self.quadrant_width - width + 1, width // 2):
            for y in range(0, self.quadrant_height - height + 1, 2):
                if not self._overlaps_with_existing(x, y, width, height, occupied):
                    return x, y
        return None

    def _try_row_fill(self, width: int, height: int, occupied: List[Dict]) -> Optional[Tuple[int, int]]:
        """Заполнение по строкам"""
        for y in range(0, self.quadrant_height - height + 1, height // 2):
            for x in range(0, self.quadrant_width - width + 1, 2):
                if not self._overlaps_with_existing(x, y, width, height, occupied):
                    return x, y
        return None

    def _try_corner_fill(self, width: int, height: int, occupied: List[Dict]) -> Optional[Tuple[int, int]]:
        """Размещение по углам"""
        corners = [
            (0, 0),  # Верхний левый
            (self.quadrant_width - width, 0),  # Верхний правый
            (0, self.quadrant_height - height),  # Нижний левый
            (self.quadrant_width - width, self.quadrant_height - height),  # Нижний правый
        ]

        for x, y in corners:
            if x >= 0 and y >= 0 and not self._overlaps_with_existing(x, y, width, height, occupied):
                return x, y
        return None

    def _overlaps_with_existing(self, x: int, y: int, width: int, height: int,
                                occupied_positions: List[Dict]) -> bool:
        """Проверка пересечения с существующими задачами"""
        new_rect = {
            'x1': x, 'y1': y,
            'x2': x + width, 'y2': y + height
        }

        for pos in occupied_positions:
            # Добавляем небольшой буфер для избежания наложения
            buffer = 1
            if (new_rect['x1'] < pos['x2'] + buffer and new_rect['x2'] > pos['x1'] - buffer and
                    new_rect['y1'] < pos['y2'] + buffer and new_rect['y2'] > pos['y1'] - buffer):
                return True

        return False

    def check_area_overflow(self, tasks: List[Task]) -> Tuple[bool, float]:
        """Проверка превышения площади квадранта"""
        total_duration = sum(t.duration if t.has_duration else 30 for t in tasks)
        area_ratio = total_duration / self.base_duration
        return area_ratio > 1.0, area_ratio

    def optimize_layout(self, tasks: List[Task]) -> List[Dict]:
        """Оптимизация размещения с проверкой площадей"""
        if not tasks:
            return []

        # Проверяем превышение площади
        overflow, ratio = self.check_area_overflow(tasks)
        if overflow:
            print(f"⚠️ Превышение площади квадранта: {ratio:.1%}")

        # Сортируем задачи: сначала длинные, потом по приоритету
        sorted_tasks = sorted(tasks,
                              key=lambda t: (
                                  -(t.duration if t.has_duration else 30),  # Длительность по убыванию
                                  -t.priority,  # Приоритет по убыванию
                                  -t.importance  # Важность по убыванию
                              ))

        layout = []
        occupied_positions = []

        for task in sorted_tasks:
            duration = task.duration if task.has_duration else 30
            width, height = self.calculate_task_dimensions(duration)
            x, y = self.find_best_position(width, height, occupied_positions)

            position = {
                'task': task,
                'x': x, 'y': y,
                'width': width, 'height': height,
                'x1': x, 'y1': y,
                'x2': x + width, 'y2': y + height
            }

            layout.append(position)
            occupied_positions.append(position)

        return layout


class FullScreenQuadrantsWidget:
    """ИСПРАВЛЕННЫЙ виджет квадрантов"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.selected_task_widget = None
        self.layout_managers = {}
        self.tooltip_window = None  # Для контроля всплывающих подсказок
        self.setup_quadrants()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_command(label="Вернуть в список", command=self.return_selected_to_list)
        self.context_menu.add_command(label="В бэклог", command=self.move_selected_to_backlog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_quadrants(self):
        """ИСПРАВЛЕННОЕ создание квадрантов"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        self.main_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Основная сетка 2x2
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack(fill='both', expand=True, padx=2, pady=2)

        # Настройка сетки
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)

        # ИСПРАВЛЕННАЯ конфигурация квадрантов
        quad_configs = [
            (0, 1, 1, "12:00", QUADRANT_COLORS[1]),  # Верхний правый - квадрант 1
            (1, 1, 2, "15:00", QUADRANT_COLORS[2]),  # Нижний правый - квадрант 2
            (1, 0, 3, "18:00", QUADRANT_COLORS[3]),  # Нижний левый - квадрант 3
            (0, 0, 4, "09:00", QUADRANT_COLORS[4])  # Верхний левый - квадрант 4
        ]

        for row, col, quad_id, time_text, color in quad_configs:
            # Основной фрейм квадранта
            quad_frame = tk.Frame(self.grid_frame, bg=color, relief='solid', bd=1)
            quad_frame.grid(row=row, column=col, sticky='nsew', padx=0, pady=0)

            # Время в углу
            time_label = tk.Label(quad_frame, text=time_text,
                                  bg=color, font=('Arial', 10, 'bold'),
                                  cursor='hand2')
            time_label.place(x=3, y=3)
            time_label.bind('<Button-1>', lambda e, q=quad_id: self.edit_time(q))

            # Область для задач - БЕЗ ОТСТУПОВ!
            task_area = tk.Frame(quad_frame, bg=color)
            task_area.place(x=0, y=20, relwidth=1.0, relheight=1.0, height=-20)

            self.quadrants[quad_id] = {
                'frame': quad_frame,
                'task_area': task_area,
                'time_label': time_label,
                'tasks': [],
                'color': color
            }

            self.layout_managers[quad_id] = QuadrantLayoutManager()
            self.setup_drop_zone(task_area, quad_id)
            self.setup_drop_zone(quad_frame, quad_id)

    def create_task_widget(self, task_area, position: Dict, quadrant: int):
        """ИСПРАВЛЕННОЕ создание виджета задачи"""
        task = position['task']
        x, y = position['x'], position['y']
        width, height = position['width'], position['height']

        color = self.quadrants[quadrant]['color']

        # Контейнер для задачи - БЕЗ ОТСТУПОВ
        task_container = tk.Frame(task_area, bg=color)
        task_container.place(x=x, y=y, width=width, height=height)

        # Основной фрейм задачи с полупрозрачностью
        task_rect = tk.Frame(task_container,
                             bg=get_priority_color(task.priority),
                             relief='solid', bd=1)
        task_rect.pack(fill='both', expand=True)

        # Применяем полупрозрачность
        original_color = get_priority_color(task.priority)
        translucent_color = self.make_color_translucent(original_color, color)
        task_rect.config(bg=translucent_color)

        # Чекбокс выполнения (только для достаточно больших задач)
        if width > 50 and height > 35:
            completed_var = tk.BooleanVar(value=task.is_completed)
            check = tk.Checkbutton(task_rect, variable=completed_var,
                                   bg=translucent_color, activebackground=translucent_color,
                                   command=lambda: self.task_manager.toggle_task_completion(
                                       task, completed_var.get()))
            check.pack(anchor='nw', padx=1, pady=1)

        # Название задачи - адаптивный размер текста
        font_size = min(9, max(7, width // 15))
        max_chars = max(3, width // 6)
        title = task.title
        if len(title) > max_chars:
            title = title[:max_chars - 2] + ".."

        task_label = tk.Label(task_rect, text=title,
                              bg=translucent_color,
                              fg='white', font=('Arial', font_size, 'bold'),
                              wraplength=max(width - 4, 40), justify='center')
        task_label.pack(expand=True, fill='both', padx=1, pady=1)

        # Информация о длительности (для больших задач)
        if task.has_duration and width > 70 and height > 50:
            duration_label = tk.Label(task_rect,
                                      text=f"{task.duration}м",
                                      bg=translucent_color,
                                      fg='white', font=('Arial', 6))
            duration_label.pack(side='bottom', pady=1)

        # События
        for widget in [task_rect, task_label]:
            widget.bind("<Button-1>", lambda e, w=task_rect, t=task: self.select_task_widget(w, t))
            widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))
            widget.bind("<B1-Motion>", lambda e, t=task: self.start_drag_task(t))

        # ИСПРАВЛЕННЫЙ Tooltip
        self.create_safe_tooltip(task_rect, self.get_task_tooltip(task))

    def make_color_translucent(self, foreground_color: str, background_color: str, alpha: float = 0.75) -> str:
        """Создание полупрозрачного цвета"""
        try:
            # Убираем #
            fg = foreground_color.lstrip('#')
            bg = background_color.lstrip('#')

            # Конвертируем в RGB
            fg_r, fg_g, fg_b = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
            bg_r, bg_g, bg_b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)

            # Смешиваем цвета
            r = int(fg_r * alpha + bg_r * (1 - alpha))
            g = int(fg_g * alpha + bg_g * (1 - alpha))
            b = int(fg_b * alpha + bg_b * (1 - alpha))

            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return foreground_color

    def start_drag_task(self, task: Task):
        """Начало перетаскивания задачи"""
        self.task_manager.start_drag_from_quadrant(task)

        # УДАЛЯЕМ задачу из квадранта при начале перетаскивания
        for quad_id, quad_data in self.quadrants.items():
            if task in quad_data['tasks']:
                quad_data['tasks'].remove(task)
                self.force_refresh_quadrant(quad_id)  # ПРИНУДИТЕЛЬНАЯ перерисовка
                break

    def force_refresh_quadrant(self, quadrant: int):
        """ПРИНУДИТЕЛЬНАЯ перерисовка квадранта"""
        if quadrant not in self.quadrants:
            return

        task_area = self.quadrants[quadrant]['task_area']

        # Удаляем все виджеты
        for widget in task_area.winfo_children():
            widget.destroy()

        # Принудительно обновляем дисплей
        task_area.update()

        tasks = self.quadrants[quadrant]['tasks']
        if not tasks:
            return

        # Получаем актуальные размеры
        self.quadrants[quadrant]['task_area'].update_idletasks()
        actual_width = task_area.winfo_width() or 350
        actual_height = task_area.winfo_height() or 250

        # Обновляем менеджер компоновки
        layout_manager = self.layout_managers[quadrant]
        layout_manager.quadrant_width = max(actual_width, 200)
        layout_manager.quadrant_height = max(actual_height, 150)
        layout_manager.total_area = layout_manager.quadrant_width * layout_manager.quadrant_height

        # Проверяем превышение площади
        overflow, ratio = layout_manager.check_area_overflow(tasks)
        if overflow:
            messagebox.showwarning("Превышение площади",
                                   f"Задачи занимают {ratio:.0%} площади квадранта!\n"
                                   f"Рекомендуется перенести часть задач в другой квадрант.")

        # Получаем оптимальную компоновку
        layout = layout_manager.optimize_layout(tasks)

        # Создаем виджеты
        for pos in layout:
            self.create_task_widget(task_area, pos, quadrant)

    def show_context_menu(self, event, task: Task):
        """Показать контекстное меню для задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        if hasattr(self, 'selected_task'):
            self.task_manager.current_task = self.selected_task
            self.task_manager.edit_current_task()

    def return_selected_to_list(self):
        """Возврат выбранной задачи в список"""
        if hasattr(self, 'selected_task'):
            task = self.selected_task
            for quad_id, quad_data in self.quadrants.items():
                if task in quad_data['tasks']:
                    self.remove_task_from_quadrant(task, quad_id)
                    break

            task.quadrant = 0
            self.task_manager.db.save_task(task)
            self.task_manager.refresh_task_list()

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if hasattr(self, 'selected_task'):
            task = self.selected_task
            for quad_id, quad_data in self.quadrants.items():
                if task in quad_data['tasks']:
                    self.remove_task_from_quadrant(task, quad_id)
                    break

            task.quadrant = 0
            task.date_scheduled = ""
            self.task_manager.db.save_task(task)
            self.task_manager.refresh_task_list()

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if hasattr(self, 'selected_task'):
            task = self.selected_task
            if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
                self.task_manager.db.delete_task(task.id)
                self.task_manager.refresh_task_list()

    def add_task_to_quadrant(self, task: Task, quadrant: int):
        """ИСПРАВЛЕННОЕ добавление задачи в квадрант"""
        if quadrant not in self.quadrants:
            return

        if task not in self.quadrants[quadrant]['tasks']:
            self.quadrants[quadrant]['tasks'].append(task)

        # ПРИНУДИТЕЛЬНАЯ перерисовка
        self.force_refresh_quadrant(quadrant)

    def refresh_quadrant_layout(self, quadrant: int):
        """Обновление компоновки квадранта - DEPRECATED, используйте force_refresh_quadrant"""
        self.force_refresh_quadrant(quadrant)

    def clear_quadrants(self):
        """Очистка всех квадрантов"""
        for quad_id in self.quadrants:
            task_area = self.quadrants[quad_id]['task_area']
            for widget in task_area.winfo_children():
                widget.destroy()
            self.quadrants[quad_id]['tasks'] = []
        self.selected_task_widget = None

    def remove_task_from_quadrant(self, task: Task, quadrant: int):
        """Удаление задачи из квадранта"""
        if quadrant in self.quadrants:
            tasks = self.quadrants[quadrant]['tasks']
            if task in tasks:
                tasks.remove(task)
                self.force_refresh_quadrant(quadrant)

    def edit_time(self, quad_id):
        current_time = self.quadrants[quad_id]['time_label']['text']
        new_time = simpledialog.askstring("Редактирование времени",
                                          f"Введите время для квадранта {quad_id}:",
                                          initialvalue=current_time)
        if new_time:
            self.quadrants[quad_id]['time_label'].config(text=new_time)

    def setup_drop_zone(self, widget, quad_id):
        def on_drop(event):
            if self.task_manager.dragged_task:
                self.task_manager.move_task_to_quadrant(
                    self.task_manager.dragged_task, quad_id)

        def on_enter(event):
            if self.task_manager.dragged_task:
                widget.config(bg='#D0D0D0')

        def on_leave(event):
            if self.task_manager.dragged_task:
                original_color = self.quadrants[quad_id]['color']
                widget.config(bg=original_color)

        widget.bind('<ButtonRelease-1>', on_drop)
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def select_task_widget(self, widget, task):
        if self.selected_task_widget:
            original_color = get_priority_color(self.selected_task_widget[1].priority)
            self.selected_task_widget[0].config(bg=original_color)

        current_color = get_priority_color(task.priority)
        darker_color = self.darken_color(current_color)
        widget.config(bg=darker_color)

        self.selected_task_widget = (widget, task)
        self.task_manager.select_task(task)

    def darken_color(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * 0.7)
        g = int(g * 0.7)
        b = int(b * 0.7)

        return f"#{r:02x}{g:02x}{b:02x}"

    def create_safe_tooltip(self, widget, text):
        """ИСПРАВЛЕННАЯ всплывающая подсказка"""

        def show_tooltip(event):
            # Закрываем предыдущую подсказку
            self.hide_tooltip()

            self.tooltip_window = tk.Toplevel()
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            self.tooltip_window.wm_attributes("-topmost", True)

            label = tk.Label(self.tooltip_window, text=text, background="lightyellow",
                             relief="solid", borderwidth=1, font=('Arial', 8),
                             justify='left', padx=5, pady=3)
            label.pack()

        def hide_tooltip_delayed(event):
            # Скрываем подсказку с задержкой
            widget.after(100, self.hide_tooltip)

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip_delayed)

    def hide_tooltip(self):
        """Скрытие всплывающей подсказки"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def get_task_tooltip(self, task: Task) -> str:
        lines = [
            f"📝 {task.title}",
            f"⭐ Важность: {task.importance}/10",
            f"🔥 Срочность: {task.priority}/10"
        ]

        if task.has_duration:
            lines.append(f"⏱️ Длительность: {task.duration} мин")
            percentage = (task.duration / 180) * 100
            lines.append(f"📊 Площадь: {percentage:.1f}%")

        return "\n".join(lines)

    def update_time_labels(self, start_hour: int):
        times = [
            (4, start_hour),
            (1, start_hour + 3),
            (2, start_hour + 6),
            (3, (start_hour + 9) % 24)
        ]

        for quad_id, hour in times:
            time_str = f"{hour:02d}:00"
            self.quadrants[quad_id]['time_label'].config(text=time_str)


# Остальные классы остаются теми же... (CompactTaskListWidget, TaskDetailPanel, etc.)
class CompactTaskListWidget:
    """Виджет списка задач с вкладками и контекстным меню"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.selected_task_widget = None
        self.setup_task_list()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню для задач"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_command(label="В бэклог", command=self.move_selected_to_backlog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_task_list(self):
        """Создание списка задач с вкладками"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Задачи")
        self.main_frame.pack(side='right', fill='y', padx=(10, 0))

        # Фиксированная ширина
        self.main_frame.configure(width=250)
        self.main_frame.pack_propagate(False)

        # Кнопка новой задачи
        ttk.Button(self.main_frame, text="+ Новая задача",
                   command=self.task_manager.create_new_task_dialog).pack(
            fill='x', padx=5, pady=(5, 0))

        # Вкладки
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка "Активные"
        self.active_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.active_frame, text="Активные")
        self.setup_task_tab(self.active_frame, "active")

        # Вкладка "Выполненные"
        self.completed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.completed_frame, text="Выполненные")
        self.setup_task_tab(self.completed_frame, "completed")

    def setup_task_tab(self, parent, tab_type):
        """Настройка вкладки с задачами"""
        # Прокручиваемый список
        canvas = tk.Canvas(parent, bg='white', width=230)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(scrollable_window, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Сохраняем ссылки
        if tab_type == "active":
            self.active_canvas = canvas
            self.active_scrollable_frame = scrollable_frame
            self.setup_drop_zone(scrollable_frame)
        else:
            self.completed_canvas = canvas
            self.completed_scrollable_frame = scrollable_frame

    def setup_drop_zone(self, widget):
        """Зона для перетаскивания задач из бэклога"""

        def on_drop(event):
            task = self.task_manager.dragged_task
            if task and not task.date_scheduled:
                self.task_manager.move_task_from_backlog(task)

        widget.bind('<ButtonRelease-1>', on_drop)

    def clear_tasks(self):
        """ПРИНУДИТЕЛЬНАЯ очистка списка задач"""
        for widget in self.active_scrollable_frame.winfo_children():
            widget.destroy()
        for widget in self.completed_scrollable_frame.winfo_children():
            widget.destroy()

        # Принудительно обновляем
        self.active_scrollable_frame.update()
        self.completed_scrollable_frame.update()

        self.selected_task_widget = None

    def add_task_button(self, task: Task):
        """Добавление блока задачи в соответствующую вкладку"""
        # Определяем, в какую вкладку добавлять
        if task.is_completed:
            parent_frame = self.completed_scrollable_frame
        else:
            parent_frame = self.active_scrollable_frame

        # Контейнер задачи
        task_container = tk.Frame(parent_frame,
                                  bg=get_priority_color(task.priority),
                                  relief='solid', bd=1, height=40)
        task_container.pack(fill='x', pady=2)
        task_container.pack_propagate(False)

        # Индикатор планирования
        if task.is_planned:
            plan_label = tk.Label(task_container, text="📅",
                                  bg=get_priority_color(task.priority),
                                  font=('Arial', 8))
            plan_label.pack(side='right', padx=2)

        # Название задачи
        title = task.title if len(task.title) <= 20 else task.title[:17] + "..."
        if task.is_completed:
            title = f"✓ {title}"

        task_label = tk.Label(task_container, text=title,
                              bg=get_priority_color(task.priority),
                              fg='white', font=('Arial', 10, 'bold'),
                              anchor='w')
        task_label.pack(fill='both', expand=True, padx=5, pady=5)

        # События
        for widget in [task_container, task_label]:
            widget.bind("<Button-1>", lambda e, t=task: self.select_task_widget(task_container, t))
            widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))

            # Перетаскивание только для активных задач
            if not task.is_completed:
                widget.bind("<B1-Motion>", lambda e, t=task: self.start_drag_task(t))

    def start_drag_task(self, task: Task):
        """Начало перетаскивания - удаляем из списка"""
        self.task_manager.start_drag_from_list(task)

        # Удаляем виджет задачи из интерфейса
        self.remove_task_widget(task)

    def remove_task_widget(self, task: Task):
        """Удаление виджета задачи из интерфейса"""
        for frame in [self.active_scrollable_frame, self.completed_scrollable_frame]:
            for widget in frame.winfo_children():
                # Проверяем, соответствует ли виджет этой задаче
                try:
                    # Находим Label с названием задачи
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and task.title in child['text']:
                            widget.destroy()
                            frame.update()  # Принудительное обновление
                            return
                except:
                    continue

    def show_context_menu(self, event, task: Task):
        """Показать контекстное меню для задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        if hasattr(self, 'selected_task'):
            self.task_manager.current_task = self.selected_task
            self.task_manager.edit_current_task()

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if hasattr(self, 'selected_task'):
            task = self.selected_task
            task.quadrant = 0
            task.date_scheduled = ""
            self.task_manager.db.save_task(task)
            self.task_manager.refresh_task_list()

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if hasattr(self, 'selected_task'):
            task = self.selected_task
            if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
                self.task_manager.db.delete_task(task.id)
                self.task_manager.refresh_task_list()

    def select_task_widget(self, widget, task):
        """Выделение виджета задачи"""
        if self.selected_task_widget:
            original_color = get_priority_color(self.selected_task_widget[1].priority)
            self.selected_task_widget[0].config(bg=original_color)
            for child in self.selected_task_widget[0].winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=original_color)

        current_color = get_priority_color(task.priority)
        darker_color = self.darken_color(current_color)
        widget.config(bg=darker_color)

        for child in widget.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg=darker_color)

        self.selected_task_widget = (widget, task)
        self.task_manager.select_task(task)

    def darken_color(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * 0.7)
        g = int(g * 0.7)
        b = int(b * 0.7)

        return f"#{r:02x}{g:02x}{b:02x}"


class TaskDetailPanel:
    """Панель отображения деталей задачи внизу"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.current_task = None
        self.is_editing = False
        self.setup_panel()

    def setup_panel(self):
        """Создание панели деталей"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Детали задачи")
        self.main_frame.pack(side='bottom', fill='x', padx=5, pady=(5, 0))

        # Основной контейнер
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Левая часть - информация
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True)

        # Название
        ttk.Label(left_frame, text="Название:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(left_frame, textvariable=self.title_var, state='readonly')
        self.title_entry.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=2)

        # Содержание
        ttk.Label(left_frame, text="Содержание:").grid(row=1, column=0, sticky='nw', pady=2)
        self.content_text = tk.Text(left_frame, height=3, state='disabled')
        self.content_text.grid(row=1, column=1, sticky='ew', padx=(5, 0), pady=2)

        # Параметры
        params_frame = ttk.Frame(left_frame)
        params_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)

        ttk.Label(params_frame, text="Важность:").grid(row=0, column=0, padx=5)
        self.importance_var = tk.IntVar()
        self.importance_spin = ttk.Spinbox(params_frame, from_=1, to=10,
                                           textvariable=self.importance_var,
                                           width=5, state='readonly')
        self.importance_spin.grid(row=0, column=1, padx=5)

        ttk.Label(params_frame, text="Срочность:").grid(row=0, column=2, padx=5)
        self.priority_var = tk.IntVar()
        self.priority_spin = ttk.Spinbox(params_frame, from_=1, to=10,
                                         textvariable=self.priority_var,
                                         width=5, state='readonly')
        self.priority_spin.grid(row=0, column=3, padx=5)

        ttk.Label(params_frame, text="Длительность:").grid(row=0, column=4, padx=5)
        self.duration_var = tk.IntVar()
        self.duration_spin = ttk.Spinbox(params_frame, from_=5, to=480,
                                         textvariable=self.duration_var,
                                         width=8, state='readonly')
        self.duration_spin.grid(row=0, column=5, padx=5)

        # Правая часть - кнопки
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='right', fill='y', padx=(10, 0))

        self.edit_btn = ttk.Button(right_frame, text="Редактировать",
                                   command=self.toggle_edit_mode)
        self.edit_btn.pack(pady=2)

        self.save_btn = ttk.Button(right_frame, text="Сохранить",
                                   command=self.save_changes, state='disabled')
        self.save_btn.pack(pady=2)

        self.cancel_btn = ttk.Button(right_frame, text="Отмена",
                                     command=self.cancel_edit, state='disabled')
        self.cancel_btn.pack(pady=2)

        # Настройка растягивания
        left_frame.grid_columnconfigure(1, weight=1)

        # Начальное состояние
        self.show_no_task()

    def show_task(self, task: Task):
        """Отображение задачи"""
        self.current_task = task

        if task:
            self.title_var.set(task.title)
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, task.content)
            self.content_text.config(state='disabled')

            self.importance_var.set(task.importance)
            self.priority_var.set(task.priority)
            self.duration_var.set(task.duration)

            self.main_frame.config(text=f"Детали задачи: {task.title[:30]}...")
            self.edit_btn.config(state='normal')
        else:
            self.show_no_task()

    def show_no_task(self):
        """Отображение пустого состояния"""
        self.title_var.set("")
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state='disabled')

        self.importance_var.set(1)
        self.priority_var.set(5)
        self.duration_var.set(30)

        self.main_frame.config(text="Детали задачи - выберите задачу")
        self.edit_btn.config(state='disabled')

    def toggle_edit_mode(self):
        """Переключение режима редактирования"""
        if self.is_editing:
            self.save_changes()
        else:
            self.enter_edit_mode()

    def enter_edit_mode(self):
        """Вход в режим редактирования"""
        self.is_editing = True

        # Разблокируем поля
        self.title_entry.config(state='normal')
        self.content_text.config(state='normal')
        self.importance_spin.config(state='normal')
        self.priority_spin.config(state='normal')
        self.duration_spin.config(state='normal')

        # Меняем кнопки
        self.edit_btn.config(text="Сохранить")
        self.save_btn.config(state='normal')
        self.cancel_btn.config(state='normal')

    def exit_edit_mode(self):
        """Выход из режима редактирования"""
        self.is_editing = False

        # Блокируем поля
        self.title_entry.config(state='readonly')
        self.content_text.config(state='disabled')
        self.importance_spin.config(state='readonly')
        self.priority_spin.config(state='readonly')
        self.duration_spin.config(state='readonly')

        # Меняем кнопки
        self.edit_btn.config(text="Редактировать")
        self.save_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')

    def save_changes(self):
        """Сохранение изменений"""
        if not self.current_task:
            return

        # Валидация
        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название не может быть пустым!")
            return

        # Сохраняем изменения
        self.current_task.title = self.title_var.get().strip()
        self.current_task.content = self.content_text.get(1.0, tk.END).strip()
        self.current_task.importance = self.importance_var.get()
        self.current_task.priority = self.priority_var.get()
        self.current_task.duration = self.duration_var.get()

        # Сохраняем в БД
        self.task_manager.db.save_task(self.current_task)

        # ПРИНУДИТЕЛЬНО обновляем интерфейс
        self.task_manager.refresh_task_list()

        self.exit_edit_mode()
        messagebox.showinfo("Успех", "Изменения сохранены!")

    def cancel_edit(self):
        """Отмена редактирования"""
        if self.current_task:
            self.show_task(self.current_task)  # Возвращаем исходные данные
        self.exit_edit_mode()


# Остальные классы остаются без изменений
class TaskEditDialog:
    """Диалог редактирования задачи"""

    def __init__(self, parent, task_manager, task=None):
        self.task_manager = task_manager
        self.task = task or Task()
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактирование задачи" if task else "Новая задача")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.load_task_data()
        self.center_window()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var)
        self.title_entry.pack(fill='x', pady=(0, 10))

        ttk.Label(main_frame, text="Содержание:").pack(anchor='w', pady=(0, 5))
        self.content_text = tk.Text(main_frame, height=4)
        self.content_text.pack(fill='x', pady=(0, 10))

        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill='x', pady=(0, 10))

        left_frame = ttk.Frame(params_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        ttk.Label(left_frame, text="Важность:").pack(anchor='w')
        self.importance_var = tk.IntVar(value=1)
        ttk.Spinbox(left_frame, from_=1, to=10, textvariable=self.importance_var,
                    width=5).pack(anchor='w', pady=(0, 10))

        ttk.Label(left_frame, text="Срочность:").pack(anchor='w')
        priority_frame = ttk.Frame(left_frame)
        priority_frame.pack(anchor='w', pady=(0, 10))

        self.priority_var = tk.IntVar(value=5)
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.priority_var,
                    width=5).pack(side='left', padx=(0, 5))
        self.priority_color_label = tk.Label(priority_frame, text="●", font=('Arial', 12))
        self.priority_color_label.pack(side='left')

        right_frame = ttk.Frame(params_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        self.has_duration_var = tk.BooleanVar()
        duration_check = ttk.Checkbutton(right_frame, text="Длительность:",
                                         variable=self.has_duration_var,
                                         command=self.toggle_duration)
        duration_check.pack(anchor='w')

        duration_frame = ttk.Frame(right_frame)
        duration_frame.pack(anchor='w', pady=(0, 10))

        self.duration_var = tk.IntVar(value=30)
        self.duration_spin = ttk.Spinbox(duration_frame, from_=5, to=480,
                                         textvariable=self.duration_var, width=8)
        self.duration_spin.pack(side='left', padx=(0, 5))
        ttk.Label(duration_frame, text="мин").pack(side='left')

        ttk.Label(right_frame, text="Тип:").pack(anchor='w')
        type_frame = ttk.Frame(right_frame)
        type_frame.pack(anchor='w', pady=(0, 10))

        self.task_type_var = tk.StringVar()
        self.task_type_combo = ttk.Combobox(type_frame, textvariable=self.task_type_var,
                                            width=15)
        self.task_type_combo.pack(side='left', padx=(0, 5))
        ttk.Button(type_frame, text="+", width=2,
                   command=self.add_task_type).pack(side='left')

        planning_frame = ttk.LabelFrame(main_frame, text="Планирование")
        planning_frame.pack(fill='x', pady=(10, 10))

        plan_content = ttk.Frame(planning_frame)
        plan_content.pack(fill='x', padx=10, pady=10)

        ttk.Label(plan_content, text="Сохранить в:").pack(side='left', padx=(0, 10))
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(plan_content, textvariable=self.date_var,
                                       values=self.get_date_options(),
                                       state='readonly', width=15)
        self.date_combo.pack(side='left', padx=(0, 10))

        self.custom_date_var = tk.StringVar()
        self.custom_date_entry = ttk.Entry(plan_content, textvariable=self.custom_date_var,
                                           state='disabled', width=12)
        self.custom_date_entry.pack(side='left')

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        ttk.Button(btn_frame, text="Сохранить", command=self.save_task).pack(side='right', padx=(0, 10))

        self.priority_var.trace('w', self.update_priority_color)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_option_selected)

        self.toggle_duration()
        self.update_priority_color()
        self.load_task_types()

    def get_date_options(self):
        options = ["Бэклог", "Сегодня", "Другая дата..."]
        last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")
        if last_choice not in options:
            options.insert(1, last_choice)
        return options

    def load_task_data(self):
        if self.task.id > 0:
            self.title_var.set(self.task.title)
            self.content_text.insert(1.0, self.task.content)
            self.importance_var.set(self.task.importance)
            self.duration_var.set(self.task.duration)
            self.has_duration_var.set(self.task.has_duration)
            self.priority_var.set(self.task.priority)

            if not self.task.date_scheduled:
                self.date_var.set("Бэклог")
            elif self.task.date_scheduled == self.task_manager.current_date.isoformat():
                self.date_var.set("Сегодня")
            else:
                self.date_var.set("Другая дата...")
                from datetime import datetime
                try:
                    task_date = datetime.strptime(self.task.date_scheduled, '%Y-%m-%d').date()
                    self.custom_date_var.set(task_date.strftime('%d.%m.%Y'))
                    self.custom_date_entry.config(state='normal')
                except:
                    pass
        else:
            last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")
            self.date_var.set(last_choice)

    def toggle_duration(self):
        state = 'normal' if self.has_duration_var.get() else 'disabled'
        self.duration_spin.config(state=state)

    def update_priority_color(self, *args):
        try:
            priority = int(self.priority_var.get())
            color = get_priority_color(priority)
            self.priority_color_label.config(fg=color)
        except:
            pass

    def on_date_option_selected(self, event=None):
        selected = self.date_var.get()
        if selected == "Другая дата...":
            self.custom_date_entry.config(state='normal')
            from datetime import datetime
            today = datetime.now().date()
            self.custom_date_var.set(today.strftime('%d.%m.%Y'))
        else:
            self.custom_date_entry.config(state='disabled')
            self.custom_date_var.set("")

    def load_task_types(self):
        task_types = self.task_manager.db.get_task_types()
        type_names = [t.name for t in task_types]
        self.task_type_combo['values'] = type_names

        if self.task.task_type_id and self.task.task_type_id <= len(task_types):
            self.task_type_var.set(task_types[self.task.task_type_id - 1].name)
        elif type_names:
            self.task_type_var.set(type_names[0])

    def add_task_type(self):
        dialog = TaskTypeDialog(self.dialog, self.task_manager.db)
        if dialog.result:
            self.load_task_types()
            self.task_type_var.set(dialog.result.name)

    def save_task(self):
        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название задачи не может быть пустым!")
            return

        task_types = self.task_manager.db.get_task_types()
        type_name = self.task_type_var.get()
        task_type_id = 1
        for t in task_types:
            if t.name == type_name:
                task_type_id = t.id
                break

        date_option = self.date_var.get()
        if date_option == "Бэклог":
            date_scheduled = ""
        elif date_option == "Сегодня":
            date_scheduled = self.task_manager.current_date.isoformat()
        elif date_option == "Другая дата...":
            try:
                from datetime import datetime
                custom_date_str = self.custom_date_var.get()
                custom_date = datetime.strptime(custom_date_str, '%d.%m.%Y').date()
                date_scheduled = custom_date.isoformat()
            except:
                messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
                return
        else:
            date_scheduled = self.task_manager.current_date.isoformat()

        self.task_manager.db.save_setting("last_save_location", date_option)

        self.task.title = self.title_var.get().strip()
        self.task.content = self.content_text.get(1.0, tk.END).strip()
        self.task.importance = self.importance_var.get()
        self.task.duration = self.duration_var.get()
        self.task.has_duration = self.has_duration_var.get()
        self.task.priority = self.priority_var.get()
        self.task.task_type_id = task_type_id
        self.task.date_scheduled = date_scheduled

        self.task.id = self.task_manager.db.save_task(self.task)

        self.result = self.task
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f'+{x}+{y}')


class TaskTypeDialog:
    """Диалог создания типа задачи"""

    def __init__(self, parent, db_manager):
        self.db = db_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Новый тип задачи")
        self.dialog.geometry("350x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var).pack(fill='x', pady=(0, 10))

        color_frame = ttk.Frame(main_frame)
        color_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(color_frame, text="Цвет:").pack(side='left')
        self.color_var = tk.StringVar(value="#2196F3")
        ttk.Entry(color_frame, textvariable=self.color_var, width=8).pack(side='left', padx=(10, 5))

        self.color_preview = tk.Label(color_frame, text="  ", bg=self.color_var.get(),
                                      relief='solid', bd=1)
        self.color_preview.pack(side='left', padx=(0, 5))

        ttk.Button(color_frame, text="Выбрать", command=self.choose_color).pack(side='left')

        ttk.Label(main_frame, text="Описание:").pack(anchor='w', pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=3)
        self.description_text.pack(fill='both', expand=True, pady=(0, 10))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        ttk.Button(btn_frame, text="Создать", command=self.create_type).pack(side='right', padx=(0, 5))

        self.color_var.trace('w', self.update_color_preview)

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])

    def update_color_preview(self, *args):
        try:
            self.color_preview.config(bg=self.color_var.get())
        except:
            pass

    def create_type(self):
        if not self.name_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название не может быть пустым!")
            return

        task_type = TaskType(
            name=self.name_var.get().strip(),
            color=self.color_var.get(),
            description=self.description_text.get(1.0, tk.END).strip()
        )

        task_type.id = self.db.save_task_type(task_type)
        self.result = task_type
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f'+{x}+{y}')


# Псевдонимы для обратной совместимости
CompactQuadrantsWidget = FullScreenQuadrantsWidget
TaskListWidget = CompactTaskListWidget
TaskEditPanel = TaskEditDialog