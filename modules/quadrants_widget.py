# -*- coding: utf-8 -*-
"""
Task Manager - Виджет квадрантов (переработанный)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from .task_models import Task
from .colors import get_priority_color, get_completed_color, QUADRANT_COLORS

logger = logging.getLogger(__name__)


class QuadrantsWidget:
    """Виджет квадрантов планирования"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.selected_task: Optional[Task] = None
        self.drag_data = {"task": None, "widget": None}
        
        self.setup_quadrants()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню для задач"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        
        # Прямые опции перемещения
        self.context_menu.add_command(label="В первый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(1))
        self.context_menu.add_command(label="Во второй квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(2))
        self.context_menu.add_command(label="В третий квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(3))
        self.context_menu.add_command(label="В четвертый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(4))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="В список задач", 
                                     command=lambda: self.move_selected_to_quadrant(0))
        self.context_menu.add_command(label="В бэклог", 
                                     command=self.move_selected_to_backlog)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_quadrants(self):
        """Создание квадрантов"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        
        # Основная сетка 2x2
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Настройка сетки
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)

        # Конфигурация квадрантов
        quad_configs = [
            (0, 0, 1, "09:00", QUADRANT_COLORS[1], "Квадрант 1"),
            (0, 1, 2, "12:00", QUADRANT_COLORS[2], "Квадрант 2"),
            (1, 1, 3, "15:00", QUADRANT_COLORS[3], "Квадрант 3"),
            (1, 0, 4, "18:00", QUADRANT_COLORS[4], "Квадрант 4")
        ]

        for row, col, quad_id, time_text, color, title in quad_configs:
            self._create_quadrant(row, col, quad_id, time_text, color, title)

    def _create_quadrant(self, row: int, col: int, quad_id: int, time_text: str, color: str, title: str):
        """Создание одного квадранта"""
        # Основной фрейм квадранта
        quad_frame = tk.Frame(self.grid_frame, bg=color, relief='solid', bd=2)
        quad_frame.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

        # Включаем возможность приема перетаскиваемых задач
        quad_frame.bind("<Enter>", lambda e, q=quad_id: self._on_quadrant_enter(e, q))
        quad_frame.bind("<Leave>", lambda e, q=quad_id: self._on_quadrant_leave(e, q))
        quad_frame.bind("<ButtonRelease-1>", lambda e, q=quad_id: self._on_quadrant_drop(e, q))

        # Заголовок с временем и номером квадранта
        header_frame = tk.Frame(quad_frame, bg=color)
        header_frame.pack(fill='x', padx=5, pady=(5, 0))

        # Название квадранта
        title_label = tk.Label(header_frame, text=title,
                              bg=color, font=('Arial', 9, 'bold'))
        title_label.pack(side='left')

        # Время
        if quad_id == 4:
            time_label = tk.Label(header_frame, text="18:00 - 21:00",
                                 bg=color, font=('Arial', 10, 'bold'))
        else:
            time_label = tk.Label(header_frame, text=time_text,
                                 bg=color, font=('Arial', 10, 'bold'))
        
        if quad_id == 1:
            time_label.config(cursor='hand2')
            time_label.bind('<Button-1>', lambda e: self.edit_start_time())
        
        time_label.pack(side='left', padx=(10, 0))

        # Информация о заполненности
        info_label = tk.Label(header_frame, text="",
                             bg=color, font=('Arial', 9))
        info_label.pack(side='right')

        # Контейнер для задач
        task_container = tk.Frame(quad_frame, bg='white')
        task_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Внутренняя таблица
        inner_table = tk.Frame(task_container, bg='white')
        inner_table.pack(fill='both', expand=True)

        # Обработчики для области задач
        task_container.bind("<ButtonRelease-1>", lambda e, q=quad_id: self._on_quadrant_drop(e, q))

        self.quadrants[quad_id] = {
            'frame': quad_frame,
            'table': inner_table,
            'container': task_container,
            'time_label': time_label,
            'info_label': info_label,
            'tasks': [],
            'color': color,
            'task_widgets': {}
        }

        self.time_labels[quad_id] = time_label

    def update_quadrants(self, quadrant_tasks: Dict[int, List[Task]]):
        """Обновление всех квадрантов"""
        logger.debug(f"Updating quadrants with tasks distribution: {[(q, len(tasks)) for q, tasks in quadrant_tasks.items()]}")
        
        # Обновляем задачи в каждом квадранте
        for quad_id in range(1, 5):
            self.quadrants[quad_id]['tasks'] = quadrant_tasks.get(quad_id, [])
            self._refresh_quadrant(quad_id)

    def _refresh_quadrant(self, quadrant: int):
        """Обновление отображения одного квадранта"""
        if quadrant not in self.quadrants:
            return
            
        quad_data = self.quadrants[quadrant]
        table = quad_data['table']
        
        # Очищаем таблицу
        for widget in table.winfo_children():
            widget.destroy()
        quad_data['task_widgets'].clear()

        tasks = quad_data['tasks']
        
        if not tasks:
            # Пустой квадрант
            empty_label = tk.Label(table, text="Перетащите задачи сюда",
                                  bg='white', fg='gray', font=('Arial', 10))
            empty_label.pack(expand=True)
            quad_data['info_label'].config(text="")
            return

        # Вычисляем оптимальное количество колонок
        num_tasks = len(tasks)
        if num_tasks <= 4:
            cols = 2
        elif num_tasks <= 9:
            cols = 3
        else:
            cols = 4

        # Размещаем задачи в таблице
        for i, task in enumerate(tasks):
            row = i // cols
            col = i % cols

            # Создаем виджет задачи
            task_widget = self._create_task_widget(table, task, quadrant)
            task_widget.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')

            # Настройка веса для равномерного распределения
            table.grid_rowconfigure(row, weight=1)
            table.grid_columnconfigure(col, weight=1)

            # Сохраняем ссылку на виджет
            quad_data['task_widgets'][task.id] = task_widget

        # Обновляем информацию о заполненности
        total_duration = sum(t.duration if t.has_duration else 30 for t in tasks)
        hours = total_duration // 60
        minutes = total_duration % 60
        info_text = f"Задач: {len(tasks)} | {hours}ч {minutes}м"
        quad_data['info_label'].config(text=info_text)

        # Предупреждение о переполнении
        if total_duration > 180:  # 3 часа
            quad_data['info_label'].config(fg='red')
        else:
            quad_data['info_label'].config(fg='black')

    def _create_task_widget(self, parent, task: Task, quadrant: int) -> tk.Frame:
        """Создание виджета для одной задачи"""
        # Определяем цвет фона
        if task.is_completed:
            bg_color = get_completed_color()
        else:
            bg_color = get_priority_color(task.priority)
            
        # Фрейм задачи
        task_frame = tk.Frame(parent, bg=bg_color, relief='raised', bd=1)

        # Контент задачи
        content_frame = tk.Frame(task_frame, bg=bg_color)
        content_frame.pack(fill='both', expand=True, padx=3, pady=3)

        # Чекбокс
        completed_var = tk.BooleanVar(value=task.is_completed)
        check = tk.Checkbutton(
            content_frame, 
            variable=completed_var,
            bg=bg_color,
            command=lambda: self.task_manager.toggle_task_completion(task, completed_var.get())
        )
        check.pack(anchor='nw')

        # Название
        title_text = task.title[:20] + "..." if len(task.title) > 20 else task.title
        title_label = tk.Label(
            content_frame, 
            text=title_text,
            bg=bg_color,
            fg='white', 
            font=('Arial', 9, 'bold'),
            wraplength=100, 
            justify='center'
        )
        title_label.pack(expand=True)

        # Длительность
        if task.has_duration:
            duration_label = tk.Label(
                content_frame, 
                text=f"{task.duration}м",
                bg=bg_color,
                fg='white', 
                font=('Arial', 8)
            )
            duration_label.pack()

        # События мыши
        for widget in [task_frame, content_frame, title_label]:
            widget.bind("<Button-1>", lambda e, t=task: self._on_task_click(e, t))
            widget.bind("<B1-Motion>", lambda e, t=task, w=task_frame: self._on_task_drag(e, t, w))
            widget.bind("<ButtonRelease-1>", lambda e: self._on_task_release(e))
            widget.bind("<Button-3>", lambda e, t=task: self._show_context_menu(e, t))

        return task_frame

    def _on_task_click(self, event, task: Task):
        """Обработка клика по задаче"""
        self.select_task(task)
        # Сохраняем начальные данные для drag & drop
        self.drag_data["task"] = task
        self.drag_data["start_x"] = event.x_root
        self.drag_data["start_y"] = event.y_root

    def _on_task_drag(self, event, task: Task, widget: tk.Widget):
        """Обработка перетаскивания задачи"""
        if not self.drag_data["widget"]:
            # Создаем плавающий виджет для визуализации перетаскивания
            self.drag_data["widget"] = tk.Toplevel(self.task_manager.root)
            self.drag_data["widget"].overrideredirect(True)
            self.drag_data["widget"].attributes("-alpha", 0.8)
            
            # Копируем внешний вид задачи
            drag_label = tk.Label(
                self.drag_data["widget"],
                text=task.title[:20] + "..." if len(task.title) > 20 else task.title,
                bg=get_priority_color(task.priority),
                fg='white',
                font=('Arial', 9, 'bold'),
                padx=10,
                pady=5
            )
            drag_label.pack()
        
        # Перемещаем плавающий виджет
        x = event.x_root - 20
        y = event.y_root - 10
        self.drag_data["widget"].geometry(f"+{x}+{y}")

    def _on_task_release(self, event):
        """Обработка отпускания задачи"""
        if self.drag_data["widget"]:
            self.drag_data["widget"].destroy()
            self.drag_data["widget"] = None

    def _on_quadrant_enter(self, event, quadrant: int):
        """Обработка входа в квадрант при перетаскивании"""
        if self.drag_data["task"]:
            # Подсветка квадранта
            self.quadrants[quadrant]['frame'].config(relief='groove', bd=4)

    def _on_quadrant_leave(self, event, quadrant: int):
        """Обработка выхода из квадранта при перетаскивании"""
        if self.drag_data["task"]:
            self.quadrants[quadrant]['frame'].config(relief='solid', bd=2)

    def _on_quadrant_drop(self, event, quadrant: int):
        """Обработка отпускания задачи в квадранте"""
        if self.drag_data["task"] and self.drag_data["task"].quadrant != quadrant:
            task = self.drag_data["task"]
            logger.info(f"Dropping task '{task.title}' into quadrant {quadrant}")
            
            # Перемещаем задачу
            self.task_manager.move_task_to_quadrant(task, quadrant)
            
            # Сбрасываем визуальные эффекты
            self.quadrants[quadrant]['frame'].config(relief='solid', bd=2)
        
        # Очищаем данные перетаскивания
        self.drag_data["task"] = None

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def _show_context_menu(self, event, task: Task):
        """Показать контекстное меню"""
        self.selected_task = task
        self.task_manager.select_task(task)
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def move_selected_to_quadrant(self, target_quadrant: int):
        """Перемещение выбранной задачи в другой квадрант"""
        if not self.selected_task:
            return

        logger.info(f"Moving selected task to quadrant {target_quadrant}")
        self.task_manager.move_task_to_quadrant(self.selected_task, target_quadrant)

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if not self.selected_task:
            return

        logger.info("Moving selected task to backlog")
        self.task_manager.move_task_to_backlog(self.selected_task)

    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        if self.selected_task:
            self.task_manager.current_task = self.selected_task
            self.task_manager.edit_current_task()

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if not self.selected_task:
            return

        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{self.selected_task.title}'?"):
            self.task_manager.task_service.delete_task(self.selected_task.id)

    def edit_start_time(self):
        """Редактирование времени начала дня"""
        current_time = self.time_labels[1]['text']
        new_time = simpledialog.askstring(
            "Редактирование времени",
            "Введите время начала дня (ЧЧ:ММ):",
            initialvalue=current_time
        )
        
        if new_time:
            try:
                time_parts = new_time.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                self.update_time_labels(hour, minute)
            except:
                messagebox.showerror("Ошибка", "Неверный формат времени! Используйте ЧЧ:ММ")

    def update_time_labels(self, start_hour: int, start_minute: int = 0):
        """Обновление времени квадрантов"""
        base_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        for quad_id in range(1, 5):
            quad_time = base_time + timedelta(hours=(quad_id - 1) * 3)
            
            if quad_id == 4:
                end_time = quad_time + timedelta(hours=3)
                time_str = f"{quad_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            else:
                time_str = quad_time.strftime('%H:%M')
            
            self.time_labels[quad_id].config(text=time_str)