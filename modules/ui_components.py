# -*- coding: utf-8 -*-
"""
Task Manager - Компоненты интерфейса
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from typing import List, Optional, Callable
from modules.task_models import Task, TaskType
from modules.colors import get_priority_color, QUADRANT_COLORS, UI_COLORS


class CompactQuadrantsWidget:
    """Компактный виджет квадрантов планирования без прокрутки"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.setup_quadrants()

    def setup_quadrants(self):
        """Создание компактной области квадрантов"""
        # Основной фрейм с фиксированным размером
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        self.main_frame.pack(side='left', fill='y', padx=(0, 10))

        # Размеры квадрантов
        QUAD_SIZE = 140  # Уменьшили размер

        # Canvas для размещения квадрантов
        canvas = tk.Canvas(self.main_frame, width=QUAD_SIZE * 2 + 40,
                           height=QUAD_SIZE * 2 + 40, bg=UI_COLORS['background'])
        canvas.pack(pady=10, padx=10)

        # Центр квадрантов
        center_x = QUAD_SIZE + 20
        center_y = QUAD_SIZE + 20

        # Метки времени (часовой циферблат)
        time_positions = [
            (center_x, 5, "12:00"),  # Сверху
            (QUAD_SIZE * 2 + 35, center_y, "15:00"),  # Справа
            (center_x, QUAD_SIZE * 2 + 35, "18:00"),  # Снизу
            (5, center_y, "09:00")  # Слева
        ]

        for x, y, time_text in time_positions:
            label = tk.Label(canvas, text=time_text, font=('Arial', 9, 'bold'),
                             bg=UI_COLORS['background'])
            canvas.create_window(x, y, window=label)
            self.time_labels[time_text] = label

        # Создаем квадранты как единый блок
        quad_configs = [
            (center_x - QUAD_SIZE // 2, 20, 1, QUADRANT_COLORS[1]),  # Верхний правый
            (center_x + 5, center_y + 5, 2, QUADRANT_COLORS[2]),  # Нижний правый
            (20, center_y + 5, 3, QUADRANT_COLORS[3]),  # Нижний левый
            (20, 20, 4, QUADRANT_COLORS[4])  # Верхний левый
        ]

        for x, y, quad_id, color in quad_configs:
            # Создаем фрейм квадранта без границ для единого блока
            frame = tk.Frame(canvas, bg=color, width=QUAD_SIZE - 5, height=QUAD_SIZE - 5)
            canvas.create_window(x, y, anchor='nw', window=frame)
            frame.pack_propagate(False)  # Фиксированный размер

            # Простая область для задач БЕЗ прокрутки
            task_area = tk.Frame(frame, bg=color)
            task_area.pack(fill='both', expand=True, padx=5, pady=5)

            self.quadrants[quad_id] = {
                'frame': frame,
                'task_area': task_area,
                'tasks': [],
                'color': color
            }

            # Настройка drop zone
            self.setup_drop_zone(task_area, quad_id)

    def setup_drop_zone(self, widget, quad_id):
        """Настройка зоны для перетаскивания"""

        def on_drop(event):
            if self.task_manager.dragged_task:
                self.task_manager.move_task_to_quadrant(
                    self.task_manager.dragged_task, quad_id)

        def on_enter(event):
            widget.config(bg='#E0E0E0')

        def on_leave(event):
            widget.config(bg=self.quadrants[quad_id]['color'])

        widget.bind('<Button-1>', on_drop)
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def update_time_labels(self, start_hour: int):
        """Обновление меток времени"""
        self.time_labels["09:00"].config(text=f"{start_hour:02d}:00")
        self.time_labels["12:00"].config(text=f"{start_hour + 3:02d}:00")
        self.time_labels["15:00"].config(text=f"{start_hour + 6:02d}:00")
        self.time_labels["18:00"].config(text=f"{start_hour + 9:02d}:00")

    def add_task_to_quadrant(self, task: Task, quadrant: int):
        """Добавление задачи в квадрант (компактно, без переполнения)"""
        if quadrant not in self.quadrants:
            return

        task_area = self.quadrants[quadrant]['task_area']

        # Проверяем количество задач - не больше 4-5 задач на квадрант
        if len(self.quadrants[quadrant]['tasks']) >= 4:
            return  # Не влезает - не влезает!

        # Создание компактной кнопки задачи
        task_btn = tk.Button(
            task_area,
            text=task.title[:12] + ("..." if len(task.title) > 12 else ""),
            bg=get_priority_color(task.priority),
            fg='white',
            font=('Arial', 8, 'bold'),
            relief='raised',
            bd=1,
            pady=1
        )
        task_btn.pack(fill='x', pady=1)

        # События
        task_btn.bind("<Double-Button-1>", lambda e: self.task_manager.select_task(task))
        self.task_manager.make_task_draggable(task_btn, task)

        # Tooltip
        self.create_tooltip(task_btn, self.get_task_tooltip(task))

        self.quadrants[quadrant]['tasks'].append(task)

    def clear_quadrants(self):
        """Очистка всех квадрантов"""
        for quad_id in self.quadrants:
            task_area = self.quadrants[quad_id]['task_area']
            for widget in task_area.winfo_children():
                widget.destroy()
            self.quadrants[quad_id]['tasks'] = []

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
            f"Приоритет: {task.priority}/10"
        ]

        if task.has_duration:
            lines.append(f"Длительность: {task.duration} мин")

        return "\n".join(lines)


class TaskListWidget:
    """Компактный виджет списка задач"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.setup_task_list()

    def setup_task_list(self):
        """Создание компактного списка задач"""
        # Фрейм с фиксированной шириной
        self.main_frame = ttk.LabelFrame(self.parent, text="Задачи")
        self.main_frame.pack(side='right', fill='both', expand=True)

        # Одна кнопка новой задачи
        ttk.Button(self.main_frame, text="+ Новая задача",
                   command=self.task_manager.create_new_task).pack(
            fill='x', padx=5, pady=(5, 0))

        # Прокручиваемый список
        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical',
                                  command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def clear_tasks(self):
        """Очистка списка задач"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def add_task_button(self, task: Task):
        """Добавление кнопки задачи"""
        task_frame = ttk.Frame(self.scrollable_frame)
        task_frame.pack(fill='x', pady=1)

        # Чекбокс выполнения
        completed_var = tk.BooleanVar(value=task.is_completed)
        ttk.Checkbutton(
            task_frame, variable=completed_var,
            command=lambda: self.task_manager.toggle_task_completion(
                task, completed_var.get())
        ).pack(side='left', padx=(0, 5))

        # Индикатор планирования
        if task.is_planned:
            plan_label = tk.Label(task_frame, text="📅", font=('Arial', 10))
            plan_label.pack(side='left', padx=(0, 3))

        # Название задачи
        task_text = task.title
        if task.is_completed:
            task_text = f"✓ {task_text}"

        task_btn = ttk.Button(
            task_frame, text=task_text,
            command=lambda: self.task_manager.select_task(task)
        )
        task_btn.pack(side='left', fill='x', expand=True)

        # Индикатор приоритета
        priority_label = tk.Label(
            task_frame, text="●", font=('Arial', 10),
            fg=get_priority_color(task.priority)
        )
        priority_label.pack(side='right', padx=(5, 0))

        # Drag & drop
        self.task_manager.make_task_draggable(task_btn, task)


class TaskEditPanel:
    """Компактная панель редактирования задач"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.setup_edit_panel()

    def setup_edit_panel(self):
        """Создание компактной панели редактирования"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Редактирование задачи")
        self.main_frame.pack(fill='x', pady=(10, 0))

        # Настройка сетки
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Название
        ttk.Label(self.main_frame, text="Название:").grid(
            row=0, column=0, sticky='w', padx=(10, 5), pady=5)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(self.main_frame, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky='ew',
                              padx=(0, 10), pady=5)

        # Содержание
        ttk.Label(self.main_frame, text="Содержание:").grid(
            row=1, column=0, sticky='nw', padx=(10, 5), pady=5)
        self.content_text = tk.Text(self.main_frame, height=3)
        self.content_text.grid(row=1, column=1, columnspan=2, sticky='ew',
                               padx=(0, 10), pady=5)

        # Параметры в горизонтальной линии
        params_frame = ttk.Frame(self.main_frame)
        params_frame.grid(row=2, column=0, columnspan=3, sticky='ew',
                          padx=10, pady=5)

        # Важность
        ttk.Label(params_frame, text="Важность:").pack(side='left', padx=(0, 5))
        self.importance_var = tk.IntVar(value=1)
        ttk.Spinbox(params_frame, from_=1, to=10, textvariable=self.importance_var,
                    width=3).pack(side='left', padx=(0, 15))

        # Приоритет
        ttk.Label(params_frame, text="Приоритет:").pack(side='left', padx=(0, 5))
        self.priority_var = tk.IntVar(value=5)
        ttk.Spinbox(params_frame, from_=1, to=10, textvariable=self.priority_var,
                    width=3).pack(side='left', padx=(0, 5))
        self.priority_color_label = tk.Label(params_frame, text="●", font=('Arial', 12))
        self.priority_color_label.pack(side='left', padx=(5, 15))

        # Длительность
        self.has_duration_var = tk.BooleanVar()
        duration_check = ttk.Checkbutton(params_frame, text="Длительность:",
                                         variable=self.has_duration_var,
                                         command=self.toggle_duration)
        duration_check.pack(side='left', padx=(0, 5))

        self.duration_var = tk.IntVar(value=30)
        self.duration_spin = ttk.Spinbox(params_frame, from_=5, to=480,
                                         textvariable=self.duration_var, width=5,
                                         state='disabled')
        self.duration_spin.pack(side='left', padx=(0, 5))
        ttk.Label(params_frame, text="мин").pack(side='left', padx=(0, 15))

        # Тип
        ttk.Label(params_frame, text="Тип:").pack(side='left', padx=(0, 5))
        self.task_type_var = tk.StringVar()
        self.task_type_combo = ttk.Combobox(params_frame, textvariable=self.task_type_var,
                                            width=10)
        self.task_type_combo.pack(side='left', padx=(0, 5))
        ttk.Button(params_frame, text="+", width=2,
                   command=self.add_task_type).pack(side='left')

        # Планирование
        planning_frame = ttk.Frame(self.main_frame)
        planning_frame.grid(row=3, column=0, columnspan=3, sticky='ew',
                            padx=10, pady=5)

        ttk.Label(planning_frame, text="Сохранить в:").pack(side='left', padx=(0, 10))
        self.date_var = tk.StringVar(value="Сегодня")
        self.date_combo = ttk.Combobox(planning_frame, textvariable=self.date_var,
                                       values=["Бэклог", "Сегодня", "Другая дата..."],
                                       state='readonly', width=12)
        self.date_combo.pack(side='left', padx=(0, 10))

        self.custom_date_var = tk.StringVar()
        self.custom_date_entry = ttk.Entry(planning_frame, textvariable=self.custom_date_var,
                                           state='disabled', width=12)
        self.custom_date_entry.pack(side='left')

        # Кнопки
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.edit_btn = ttk.Button(btn_frame, text="Редактировать",
                                   command=self.task_manager.toggle_edit_mode)
        self.edit_btn.pack(side='left', padx=(0, 5))

        self.save_btn = ttk.Button(btn_frame, text="Сохранить",
                                   command=self.task_manager.save_current_task)
        self.save_btn.pack(side='left', padx=(0, 5))

        self.delete_btn = ttk.Button(btn_frame, text="Удалить",
                                     command=self.task_manager.delete_current_task)
        self.delete_btn.pack(side='left')

        # Привязка событий
        self.priority_var.trace('w', self.update_priority_color)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_option_selected)

        # Инициализация
        self.set_edit_mode(False)
        self.update_priority_color()

    def toggle_duration(self):
        """Переключение активности поля длительности"""
        state = 'normal' if self.has_duration_var.get() else 'disabled'
        self.duration_spin.config(state=state)

    def update_priority_color(self, *args):
        """Обновление цвета приоритета"""
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

    def add_task_type(self):
        """Добавление нового типа задачи"""
        dialog = TaskTypeDialog(self.parent, self.task_manager.db)
        if dialog.result:
            self.load_task_types()
            self.task_type_var.set(dialog.result.name)

    def load_task_types(self):
        """Загрузка типов задач"""
        task_types = self.task_manager.db.get_task_types()
        type_names = [t.name for t in task_types]
        self.task_type_combo['values'] = type_names

    def set_edit_mode(self, enabled: bool):
        """Установка режима редактирования"""
        state = 'normal' if enabled else 'disabled'
        self.title_entry.config(state=state)
        self.content_text.config(state=state)

        text = "Отменить редактирование" if enabled else "Редактировать"
        self.edit_btn.config(text=text)


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