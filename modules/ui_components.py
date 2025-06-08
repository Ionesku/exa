# -*- coding: utf-8 -*-
"""
Task Manager - Компоненты интерфейса (обновленная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
from typing import List, Optional, Callable
from .task_models import Task, TaskType
from .colors import get_priority_color, QUADRANT_COLORS, UI_COLORS


class FullScreenQuadrantsWidget:
    """Квадранты на весь экран с временем внутри"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.selected_task_widget = None
        self.setup_quadrants()

    def setup_quadrants(self):
        """Создание квадрантов на весь экран"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        self.main_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Основная сетка 2x2
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Настройка сетки - каждая ячейка растягивается
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)

        # Конфигурация квадрантов
        quad_configs = [
            (0, 1, 1, "12:00", QUADRANT_COLORS[1]),  # Верхний правый
            (1, 1, 2, "15:00", QUADRANT_COLORS[2]),  # Нижний правый
            (1, 0, 3, "18:00", QUADRANT_COLORS[3]),  # Нижний левый
            (0, 0, 4, "09:00", QUADRANT_COLORS[4])  # Верхний левый
        ]

        for row, col, quad_id, time_text, color in quad_configs:
            # Основной фрейм квадранта
            quad_frame = tk.Frame(self.grid_frame, bg=color, relief='solid', bd=2)
            quad_frame.grid(row=row, column=col, sticky='nsew', padx=1, pady=1)

            # Время в углу
            time_label = tk.Label(quad_frame, text=time_text,
                                  bg=color, font=('Arial', 10, 'bold'),
                                  cursor='hand2')
            time_label.place(x=5, y=5)

            # Делаем время кликабельным для редактирования
            time_label.bind('<Button-1>', lambda e, q=quad_id: self.edit_time(q))

            # Область для задач
            task_area = tk.Frame(quad_frame, bg=color)
            task_area.pack(fill='both', expand=True, padx=25, pady=25)
            # Позволяем размещать задачи сеткой
            for i in range(4):
                task_area.grid_columnconfigure(i, weight=1)

            self.quadrants[quad_id] = {
                'frame': quad_frame,
                'task_area': task_area,
                'time_label': time_label,
                'tasks': [],
                'color': color
            }
            self.time_labels[time_text] = time_label

            # Настройка drop zone
            self.setup_drop_zone(task_area, quad_id)
            self.setup_drop_zone(quad_frame, quad_id)

    def edit_time(self, quad_id):
        """Редактирование времени для квадранта"""
        current_time = self.quadrants[quad_id]['time_label']['text']
        new_time = simpledialog.askstring("Редактирование времени",
                                          f"Введите время для квадранта {quad_id}:",
                                          initialvalue=current_time)
        if new_time:
            self.quadrants[quad_id]['time_label'].config(text=new_time)

    def setup_drop_zone(self, widget, quad_id):
        """Настройка зоны для перетаскивания"""

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

    def update_time_labels(self, start_hour: int):
        """Обновление меток времени"""
        times = [
            (4, start_hour),  # 09:00 -> start_hour
            (1, start_hour + 3),  # 12:00 -> start_hour + 3
            (2, start_hour + 6),  # 15:00 -> start_hour + 6
            (3, (start_hour + 9) % 24)  # 18:00 -> start_hour + 9, с обработкой переполнения
        ]

        for quad_id, hour in times:
            time_str = f"{hour:02d}:00"
            self.quadrants[quad_id]['time_label'].config(text=time_str)

    def add_task_to_quadrant(self, task: Task, quadrant: int):
        """Добавление задачи в квадрант как квадрат по длительности"""
        if quadrant not in self.quadrants:
            return

        task_area = self.quadrants[quadrant]['task_area']
        color = self.quadrants[quadrant]['color']

        # Размер квадрата зависит от длительности (базовый размер = 30 минут)
        duration = task.duration if task.has_duration else 30
        base_side = 60
        side = int(base_side * (duration / 30) ** 0.5)
        side = max(40, min(side, 120))

        index = len(self.quadrants[quadrant]['tasks'])
        row = index // 4
        column = index % 4

        # Контейнер для задачи
        task_container = tk.Frame(task_area, bg=color, width=side, height=side)
        task_container.grid(row=row, column=column, padx=2, pady=2, sticky='nsew')
        task_container.grid_propagate(False)

        # Квадрат задачи
        task_rect = tk.Frame(task_container,
                             bg=get_priority_color(task.priority),
                             relief='solid', bd=2)
        task_rect.pack(fill='both', expand=True)
        task_rect.pack_propagate(False)

        # Чекбокс выполнения
        completed_var = tk.BooleanVar(value=task.is_completed)
        check = tk.Checkbutton(task_rect, variable=completed_var,
                               bg=get_priority_color(task.priority),
                               command=lambda: self.task_manager.toggle_task_completion(
                                   task, completed_var.get()))
        check.pack(anchor='nw', padx=2, pady=2)

        # Название задачи
        title = task.title if len(task.title) <= 15 else task.title[:12] + "..."
        task_label = tk.Label(task_rect, text=title,
                              bg=get_priority_color(task.priority),
                              fg='white', font=('Arial', 9, 'bold'),
                              wraplength=side-10, justify='center')
        task_label.pack(expand=True, padx=5, pady=5)

        # События
        for widget in [task_rect, task_label]:
            widget.bind("<Button-1>", lambda e, w=task_rect, t=task: self.select_task_widget(w, t))
            widget.bind("<Button-3>", lambda e, t=task: self.return_task_to_list(t))
            widget.bind("<B1-Motion>", lambda e, t=task: self.task_manager.start_drag_from_quadrant(t))

        # Tooltip
        self.create_tooltip(task_rect, self.get_task_tooltip(task))

        self.quadrants[quadrant]['tasks'].append((task, task_container))

    def select_task_widget(self, widget, task):
        """Выделение виджета задачи"""
        # Снимаем выделение с предыдущего
        if self.selected_task_widget:
            original_color = get_priority_color(self.selected_task_widget[1].priority)
            self.selected_task_widget[0].config(bg=original_color)

        # Выделяем текущий (делаем темнее)
        current_color = get_priority_color(task.priority)
        darker_color = self.darken_color(current_color)
        widget.config(bg=darker_color)

        self.selected_task_widget = (widget, task)
        self.task_manager.select_task(task)

    def darken_color(self, hex_color: str) -> str:
        """Затемнение цвета"""
        # Убираем #
        hex_color = hex_color.lstrip('#')

        # Конвертируем в RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Затемняем на 30%
        r = int(r * 0.7)
        g = int(g * 0.7)
        b = int(b * 0.7)

        return f"#{r:02x}{g:02x}{b:02x}"

    def return_task_to_list(self, task):
        """Возврат задачи в список по правому клику"""
        task.quadrant = 0
        self.task_manager.db.save_task(task)
        self.task_manager.refresh_task_list()

    def clear_quadrants(self):
        """Очистка всех квадрантов"""
        for quad_id in self.quadrants:
            task_area = self.quadrants[quad_id]['task_area']
            for widget in task_area.winfo_children():
                widget.destroy()
            self.quadrants[quad_id]['tasks'] = []

        self.selected_task_widget = None

    def create_tooltip(self, widget, text):
        """Простая всплывающая подсказка"""

        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(tooltip, text=text, background="lightyellow",
                             relief="solid", borderwidth=1, font=('Arial', 9))
            label.pack()

            widget.tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def get_task_tooltip(self, task: Task) -> str:
        """Текст подсказки для задачи"""
        lines = [
            f"Название: {task.title}",
            f"Важность: {task.importance}/10",
            f"Срочность: {task.priority}/10"
        ]

        if task.has_duration:
            lines.append(f"Длительность: {task.duration} мин")

        return "\n".join(lines)


class CompactTaskListWidget:
    """Компактный виджет списка задач без кнопок"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.selected_task_widget = None
        self.setup_task_list()
        self.setup_drop_zone()

    def setup_task_list(self):
        """Создание компактного списка задач"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Задачи")
        self.main_frame.pack(side='right', fill='y', padx=(10, 0))

        # Фиксированная ширина
        self.main_frame.configure(width=250)
        self.main_frame.pack_propagate(False)

        # Кнопка новой задачи
        ttk.Button(self.main_frame, text="+ Новая задача",
                   command=self.task_manager.create_new_task_dialog).pack(
            fill='x', padx=5, pady=(5, 0))

        # Прокручиваемый список
        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg='white', width=230)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical',
                                  command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.scrollable_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.scrollable_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_drop_zone(self):
        """Зона для перетаскивания задач из бэклога"""

        def on_drop(event):
            task = self.task_manager.dragged_task
            if task and not task.date_scheduled:
                self.task_manager.move_task_from_backlog(task)

        self.scrollable_frame.bind('<ButtonRelease-1>', on_drop)


    def clear_tasks(self):
        """Очистка списка задач"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_task_widget = None

    def add_task_button(self, task: Task):
        """Добавление блока задачи без кнопок"""
        # Контейнер задачи
        task_container = tk.Frame(self.scrollable_frame,
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
            widget.bind("<Button-1>", lambda e: self.select_task_widget(task_container, task))
            widget.bind("<B1-Motion>", lambda e: self.task_manager.start_drag_from_list(task))

        # Tooltip
        self.create_tooltip(task_container, self.get_task_tooltip(task))

    def select_task_widget(self, widget, task):
        """Выделение виджета задачи"""
        # Снимаем выделение с предыдущего
        if self.selected_task_widget:
            original_color = get_priority_color(self.selected_task_widget[1].priority)
            self.selected_task_widget[0].config(bg=original_color)
            # Также обновляем label внутри
            for child in self.selected_task_widget[0].winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=original_color)

        # Выделяем текущий (делаем темнее)
        current_color = get_priority_color(task.priority)
        darker_color = self.darken_color(current_color)
        widget.config(bg=darker_color)

        # Обновляем цвет детей
        for child in widget.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg=darker_color)

        self.selected_task_widget = (widget, task)
        self.task_manager.select_task(task)

    def darken_color(self, hex_color: str) -> str:
        """Затемнение цвета"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * 0.7)
        g = int(g * 0.7)
        b = int(b * 0.7)

        return f"#{r:02x}{g:02x}{b:02x}"

    def create_tooltip(self, widget, text):
        """Всплывающая подсказка"""

        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(tooltip, text=text, background="lightyellow",
                             relief="solid", borderwidth=1, font=('Arial', 9))
            label.pack()

            widget.tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def get_task_tooltip(self, task: Task) -> str:
        """Текст подсказки для задачи"""
        lines = [
            f"Название: {task.title}",
            f"Важность: {task.importance}/10",
            f"Срочность: {task.priority}/10"
        ]

        if task.has_duration:
            lines.append(f"Длительность: {task.duration} мин")

        if task.is_planned:
            lines.append(f"Запланировано в квадрант {task.quadrant}")

        return "\n".join(lines)


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
        """Настройка интерфейса диалога"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Название
        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var)
        self.title_entry.pack(fill='x', pady=(0, 10))

        # Содержание
        ttk.Label(main_frame, text="Содержание:").pack(anchor='w', pady=(0, 5))
        self.content_text = tk.Text(main_frame, height=4)
        self.content_text.pack(fill='x', pady=(0, 10))

        # Параметры в две колонки
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill='x', pady=(0, 10))

        # Левая колонка
        left_frame = ttk.Frame(params_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Важность
        ttk.Label(left_frame, text="Важность:").pack(anchor='w')
        self.importance_var = tk.IntVar(value=1)
        ttk.Spinbox(left_frame, from_=1, to=10, textvariable=self.importance_var,
                    width=5).pack(anchor='w', pady=(0, 10))

        # Срочность
        ttk.Label(left_frame, text="Срочность:").pack(anchor='w')
        priority_frame = ttk.Frame(left_frame)
        priority_frame.pack(anchor='w', pady=(0, 10))

        self.priority_var = tk.IntVar(value=5)
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.priority_var,
                    width=5).pack(side='left', padx=(0, 5))
        self.priority_color_label = tk.Label(priority_frame, text="●", font=('Arial', 12))
        self.priority_color_label.pack(side='left')

        # Правая колонка
        right_frame = ttk.Frame(params_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        # Длительность
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

        # Тип задачи
        ttk.Label(right_frame, text="Тип:").pack(anchor='w')
        type_frame = ttk.Frame(right_frame)
        type_frame.pack(anchor='w', pady=(0, 10))

        self.task_type_var = tk.StringVar()
        self.task_type_combo = ttk.Combobox(type_frame, textvariable=self.task_type_var,
                                            width=15)
        self.task_type_combo.pack(side='left', padx=(0, 5))
        ttk.Button(type_frame, text="+", width=2,
                   command=self.add_task_type).pack(side='left')

        # Планирование
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

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        ttk.Button(btn_frame, text="Сохранить", command=self.save_task).pack(side='right', padx=(0, 10))

        # Привязка событий
        self.priority_var.trace('w', self.update_priority_color)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_option_selected)

        # Инициализация
        self.toggle_duration()
        self.update_priority_color()
        self.load_task_types()

    def get_date_options(self):
        """Получение опций для сохранения с учетом последнего выбора"""
        options = ["Бэклог", "Сегодня", "Другая дата..."]
        # Загружаем последний выбор из настроек
        last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")

        # Если последний выбор не в списке, добавляем его
        if last_choice not in options:
            options.insert(1, last_choice)

        return options

    def load_task_data(self):
        """Загрузка данных задачи"""
        if self.task.id > 0:  # Редактирование
            self.title_var.set(self.task.title)
            self.content_text.insert(1.0, self.task.content)
            self.importance_var.set(self.task.importance)
            self.duration_var.set(self.task.duration)
            self.has_duration_var.set(self.task.has_duration)
            self.priority_var.set(self.task.priority)

            # Установка даты планирования
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
        else:  # Новая задача
            # Загружаем последний выбор места сохранения
            last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")
            self.date_var.set(last_choice)

    def toggle_duration(self):
        """Переключение активности поля длительности"""
        state = 'normal' if self.has_duration_var.get() else 'disabled'
        self.duration_spin.config(state=state)

    def update_priority_color(self, *args):
        """Обновление цвета срочности"""
        try:
            priority = int(self.priority_var.get())
            color = get_priority_color(priority)
            self.priority_color_label.config(fg=color)
        except:
            pass

    def on_date_option_selected(self, event=None):
        """Обработка выбора опции даты"""
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
        """Загрузка типов задач"""
        task_types = self.task_manager.db.get_task_types()
        type_names = [t.name for t in task_types]
        self.task_type_combo['values'] = type_names

        if self.task.task_type_id and self.task.task_type_id <= len(task_types):
            self.task_type_var.set(task_types[self.task.task_type_id - 1].name)
        elif type_names:
            self.task_type_var.set(type_names[0])

    def add_task_type(self):
        """Добавление нового типа задачи"""
        dialog = TaskTypeDialog(self.dialog, self.task_manager.db)
        if dialog.result:
            self.load_task_types()
            self.task_type_var.set(dialog.result.name)

    def save_task(self):
        """Сохранение задачи"""
        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название задачи не может быть пустым!")
            return

        # Получение типа задачи
        task_types = self.task_manager.db.get_task_types()
        type_name = self.task_type_var.get()
        task_type_id = 1
        for t in task_types:
            if t.name == type_name:
                task_type_id = t.id
                break

        # Определение даты планирования
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

        # Сохраняем последний выбор места сохранения
        self.task_manager.db.save_setting("last_save_location", date_option)

        # Обновление данных задачи
        self.task.title = self.title_var.get().strip()
        self.task.content = self.content_text.get(1.0, tk.END).strip()
        self.task.importance = self.importance_var.get()
        self.task.duration = self.duration_var.get()
        self.task.has_duration = self.has_duration_var.get()
        self.task.priority = self.priority_var.get()
        self.task.task_type_id = task_type_id
        self.task.date_scheduled = date_scheduled

        # Сохранение в БД
        self.task.id = self.task_manager.db.save_task(self.task)

        self.result = self.task
        self.dialog.destroy()

    def cancel(self):
        """Отмена"""
        self.dialog.destroy()

    def center_window(self):
        """Центрирование окна"""
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
        """Настройка интерфейса"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Название
        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var).pack(fill='x', pady=(0, 10))

        # Цвет
        color_frame = ttk.Frame(main_frame)
        color_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(color_frame, text="Цвет:").pack(side='left')
        self.color_var = tk.StringVar(value="#2196F3")
        ttk.Entry(color_frame, textvariable=self.color_var, width=8).pack(side='left', padx=(10, 5))

        self.color_preview = tk.Label(color_frame, text="  ", bg=self.color_var.get(),
                                      relief='solid', bd=1)
        self.color_preview.pack(side='left', padx=(0, 5))

        ttk.Button(color_frame, text="Выбрать", command=self.choose_color).pack(side='left')

        # Описание
        ttk.Label(main_frame, text="Описание:").pack(anchor='w', pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=3)
        self.description_text.pack(fill='both', expand=True, pady=(0, 10))

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        ttk.Button(btn_frame, text="Создать", command=self.create_type).pack(side='right', padx=(0, 5))

        self.color_var.trace('w', self.update_color_preview)

    def choose_color(self):
        """Выбор цвета"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])

    def update_color_preview(self, *args):
        """Обновление превью цвета"""
        try:
            self.color_preview.config(bg=self.color_var.get())
        except:
            pass

    def create_type(self):
        """Создание типа"""
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
        """Отмена"""
        self.dialog.destroy()

    def center_window(self):
        """Центрирование окна"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f'+{x}+{y}')


# Псевдонимы для обратной совместимости
CompactQuadrantsWidget = FullScreenQuadrantsWidget
TaskListWidget = CompactTaskListWidget
TaskEditPanel = TaskEditDialog