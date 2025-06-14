# -*- coding: utf-8 -*-
"""
Task Manager - Виджет списка задач
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .task_models import Task
from .colors import get_priority_color


class TaskListWidget:
    """Виджет списка задач с вкладками"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.selected_task = None
        self.setup_task_list()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        
        # Прямые опции перемещения без вложенности
        self.context_menu.add_command(label="В первый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(1))
        self.context_menu.add_command(label="Во второй квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(2))
        self.context_menu.add_command(label="В третий квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(3))
        self.context_menu.add_command(label="В четвертый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(4))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="В бэклог", 
                                     command=self.move_selected_to_backlog)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_task_list(self):
        """Создание списка задач"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Задачи")
        self.main_frame.pack(side='right', fill='y')

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
        else:
            self.completed_canvas = canvas
            self.completed_scrollable_frame = scrollable_frame

    def clear_tasks(self):
        """Очистка списка задач"""
        for widget in self.active_scrollable_frame.winfo_children():
            widget.destroy()
        for widget in self.completed_scrollable_frame.winfo_children():
            widget.destroy()

    def add_task(self, task: Task):
        """Добавление задачи в список"""
        # Определяем родительский фрейм
        if task.is_completed:
            parent_frame = self.completed_scrollable_frame
        else:
            parent_frame = self.active_scrollable_frame

        # Контейнер задачи
        task_frame = tk.Frame(parent_frame,
                             bg=get_priority_color(task.priority),
                             relief='solid', bd=1, height=40)
        task_frame.pack(fill='x', pady=2)
        task_frame.pack_propagate(False)

        # Индикатор планирования
        if task.is_planned:
            plan_label = tk.Label(task_frame, text="📅",
                                 bg=get_priority_color(task.priority),
                                 font=('Arial', 8))
            plan_label.pack(side='right', padx=2)

        # Название
        title = task.title if len(task.title) <= 20 else task.title[:17] + "..."
        if task.is_completed:
            title = f"✓ {title}"

        title_label = tk.Label(task_frame, text=title,
                              bg=get_priority_color(task.priority),
                              fg='white', font=('Arial', 10, 'bold'),
                              anchor='w')
        title_label.pack(fill='both', expand=True, padx=5, pady=5)

        # События
        for widget in [task_frame, title_label]:
            widget.bind("<Button-1>", lambda e, t=task: self.select_task(t))
            widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def show_context_menu(self, event, task: Task):
        """Показать контекстное меню"""
        self.selected_task = task
        self.task_manager.select_task(task)
        
        # Закрываем меню по правому клику
        def close_menu(e):
            self.context_menu.unpost()
        
        self.context_menu.bind("<Button-3>", close_menu)
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def move_selected_to_quadrant(self, quadrant: int):
        """Перемещение выбранной задачи в квадрант"""
        if self.selected_task:
            self.task_manager.move_task_to_quadrant(self.selected_task, quadrant)

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if self.selected_task:
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