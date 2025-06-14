# -*- coding: utf-8 -*-
"""
Task Manager - Виджет квадрантов с табличным отображением
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List
from .task_models import Task
from .colors import get_priority_color, QUADRANT_COLORS


class QuadrantsWidget:
    """Виджет квадрантов планирования"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.selected_task = None
        self.setup_quadrants()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню для задач"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        
        # Подменю для перемещения
        move_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Переместить", menu=move_menu)
        
        move_menu.add_command(label="В первый квадрант", 
                             command=lambda: self.move_selected_to_quadrant(1))
        move_menu.add_command(label="Во второй квадрант", 
                             command=lambda: self.move_selected_to_quadrant(2))
        move_menu.add_command(label="В третий квадрант", 
                             command=lambda: self.move_selected_to_quadrant(3))
        move_menu.add_command(label="В четвертый квадрант", 
                             command=lambda: self.move_selected_to_quadrant(4))
        move_menu.add_separator()
        move_menu.add_command(label="В список задач", 
                             command=lambda: self.move_selected_to_quadrant(0))
        move_menu.add_command(label="В бэклог", 
                             command=self.move_selected_to_backlog)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_quadrants(self):
        """Создание квадрантов"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        self.main_frame.pack(side='left', fill='both', expand=True)

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
            (0, 1, 1, "12:00", QUADRANT_COLORS[1]),  # Верхний правый
            (1, 1, 2, "15:00", QUADRANT_COLORS[2]),  # Нижний правый
            (1, 0, 3, "18:00", QUADRANT_COLORS[3]),  # Нижний левый
            (0, 0, 4, "09:00", QUADRANT_COLORS[4])   # Верхний левый
        ]

        for row, col, quad_id, time_text, color in quad_configs:
            # Фрейм квадранта
            quad_frame = tk.Frame(self.grid_frame, bg=color, relief='solid', bd=2)
            quad_frame.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

            # Заголовок с временем
            header_frame = tk.Frame(quad_frame, bg=color)
            header_frame.pack(fill='x', padx=5, pady=(5, 0))

            time_label = tk.Label(header_frame, text=time_text,
                                 bg=color, font=('Arial', 11, 'bold'),
                                 cursor='hand2')
            time_label.pack(side='left')
            time_label.bind('<Button-1>', lambda e, q=quad_id: self.edit_time(q))

            # Информация о заполненности
            info_label = tk.Label(header_frame, text="",
                                 bg=color, font=('Arial', 9))
            info_label.pack(side='right')

            # Таблица для задач
            table_frame = tk.Frame(quad_frame, bg='white')
            table_frame.pack(fill='both', expand=True, padx=5, pady=5)

            # Создаем внутреннюю таблицу
            inner_table = tk.Frame(table_frame, bg='white')
            inner_table.pack(fill='both', expand=True)

            self.quadrants[quad_id] = {
                'frame': quad_frame,
                'table': inner_table,
                'time_label': time_label,
                'info_label': info_label,
                'tasks': [],
                'color': color,
                'task_widgets': {}
            }

            self.time_labels[quad_id] = time_label

    def add_task_to_quadrant(self, task: Task, quadrant: int):
        """Добавление задачи в квадрант"""
        if quadrant not in self.quadrants:
            return

        quad_data = self.quadrants[quadrant]
        
        # Добавляем задачу если её еще нет
        if task not in quad_data['tasks']:
            quad_data['tasks'].append(task)

        # Обновляем отображение
        self.refresh_quadrant(quadrant)

    def refresh_quadrant(self, quadrant: int):
        """Обновление отображения квадранта"""
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

            # Фрейм задачи
            task_frame = tk.Frame(table, bg=get_priority_color(task.priority),
                                 relief='raised', bd=1)
            task_frame.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')

            # Настройка веса для равномерного распределения
            table.grid_rowconfigure(row, weight=1)
            table.grid_columnconfigure(col, weight=1)

            # Контент задачи
            content_frame = tk.Frame(task_frame, bg=get_priority_color(task.priority))
            content_frame.pack(fill='both', expand=True, padx=3, pady=3)

            # Чекбокс
            completed_var = tk.BooleanVar(value=task.is_completed)
            check = tk.Checkbutton(content_frame, variable=completed_var,
                                  bg=get_priority_color(task.priority),
                                  command=lambda t=task, v=completed_var: 
                                  self.task_manager.toggle_task_completion(t, v.get()))
            check.pack(anchor='nw')

            # Название
            title_label = tk.Label(content_frame, text=task.title[:20] + "..." if len(task.title) > 20 else task.title,
                                  bg=get_priority_color(task.priority),
                                  fg='white', font=('Arial', 9, 'bold'),
                                  wraplength=100, justify='center')
            title_label.pack(expand=True)

            # Длительность
            if task.has_duration:
                duration_label = tk.Label(content_frame, text=f"{task.duration}м",
                                        bg=get_priority_color(task.priority),
                                        fg='white', font=('Arial', 8))
                duration_label.pack()

            # События
            for widget in [task_frame, content_frame, title_label]:
                widget.bind("<Button-1>", lambda e, t=task: self.select_task(t))
                widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))

            # Сохраняем ссылку на виджет
            quad_data['task_widgets'][task.id] = task_frame

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

    def clear_quadrants(self):
        """Очистка всех квадрантов"""
        for quad_id in self.quadrants:
            self.quadrants[quad_id]['tasks'].clear()
            self.refresh_quadrant(quad_id)

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def show_context_menu(self, event, task: Task):
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

        # Находим текущий квадрант
        current_quadrant = None
        for quad_id, quad_data in self.quadrants.items():
            if self.selected_task in quad_data['tasks']:
                current_quadrant = quad_id
                quad_data['tasks'].remove(self.selected_task)
                break

        # Перемещаем задачу
        self.task_manager.move_task_to_quadrant(self.selected_task, target_quadrant)

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if not self.selected_task:
            return

        # Удаляем из текущего квадранта
        for quad_id, quad_data in self.quadrants.items():
            if self.selected_task in quad_data['tasks']:
                quad_data['tasks'].remove(self.selected_task)
                break

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
            self.task_manager.db.delete_task(self.selected_task.id)
            self.task_manager.refresh_all()

    def edit_time(self, quad_id: int):
        """Редактирование времени квадранта"""
        current_time = self.time_labels[quad_id]['text']
        new_time = simpledialog.askstring("Редактирование времени",
                                         f"Введите время для квадранта {quad_id}:",
                                         initialvalue=current_time)
        if new_time:
            self.time_labels[quad_id].config(text=new_time)

    def update_time_labels(self, start_hour: int):
        """Обновление времени квадрантов"""
        times = [
            (4, f"{start_hour:02d}:00"),
            (1, f"{(start_hour + 3) % 24:02d}:00"),
            (2, f"{(start_hour + 6) % 24:02d}:00"),
            (3, f"{(start_hour + 9) % 24:02d}:00")
        ]

        for quad_id, time_str in times:
            self.time_labels[quad_id].config(text=time_str)