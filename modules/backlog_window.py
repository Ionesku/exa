# -*- coding: utf-8 -*-
"""
Task Manager - Окно бэклога
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .task_models import Task
from .task_edit_dialog import TaskEditDialog
from .colors import get_priority_color
from .utils import TaskUtils


class BacklogWindow:
    """Окно бэклога с группировкой по типам"""

    def __init__(self, parent, db_manager, task_manager=None):
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Бэклог задач")
        self.window.geometry("800x600")

        self.setup_ui()
        self.load_backlog()

    def setup_ui(self):
        """Создание интерфейса"""
        # Заголовок
        ttk.Label(self.window, text="Бэклог задач",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Основной контейнер
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Notebook для типов задач
        self.types_notebook = ttk.Notebook(main_frame)
        self.types_notebook.pack(fill='both', expand=True)

        # Кнопка создания новой задачи
        ttk.Button(self.window, text="+ Новая задача в бэклог",
                   command=self.create_backlog_task).pack(pady=10)

    def load_backlog(self):
        """Загрузка задач из бэклога"""
        # Получение задач
        backlog_tasks = self.db.get_tasks(include_backlog=True)
        backlog_tasks = [t for t in backlog_tasks if not t.date_scheduled]

        if not backlog_tasks:
            # Пустой бэклог
            empty_frame = ttk.Frame(self.types_notebook)
            self.types_notebook.add(empty_frame, text="Пусто")
            ttk.Label(empty_frame, text="Нет задач в бэклоге",
                     font=('Arial', 12)).pack(expand=True)
            return

        # Группировка по типам
        task_types = self.db.get_task_types()
        grouped_tasks = TaskUtils.group_tasks_by_type(backlog_tasks, task_types)

        # Создание вкладок для каждого типа
        for type_name, tasks in grouped_tasks.items():
            self.create_type_tab(type_name, tasks)

    def create_type_tab(self, type_name: str, tasks: list):
        """Создание вкладки для типа задач"""
        # Фрейм вкладки
        type_frame = ttk.Frame(self.types_notebook)
        self.types_notebook.add(type_frame, text=f"{type_name} ({len(tasks)})")

        # Прокручиваемый список
        canvas_frame = ttk.Frame(type_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Отображение задач
        for task in tasks:
            self.create_task_widget(scrollable_frame, task)

    def create_task_widget(self, parent, task: Task):
        """Создание виджета задачи"""
        # Контейнер задачи
        task_frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        task_frame.pack(fill='x', pady=2, padx=2)

        # Заголовок
        header_frame = ttk.Frame(task_frame)
        header_frame.pack(fill='x', padx=5, pady=2)

        # Индикатор приоритета
        priority_label = tk.Label(header_frame, text="●",
                                  fg=get_priority_color(task.priority),
                                  font=('Arial', 12))
        priority_label.pack(side='left', padx=(0, 5))

        # Название
        title_label = ttk.Label(header_frame, text=task.title, font=('Arial', 10, 'bold'))
        title_label.pack(side='left', fill='x', expand=True)

        # Информация
        info_frame = ttk.Frame(task_frame)
        info_frame.pack(fill='x', padx=5, pady=2)

        info_text = f"Важность: {task.importance}/10 | Срочность: {task.priority}/10"
        if task.has_duration:
            info_text += f" | Длительность: {task.duration} мин"

        ttk.Label(info_frame, text=info_text, font=('Arial', 8)).pack(side='left')

        # Кнопки
        btn_frame = ttk.Frame(task_frame)
        btn_frame.pack(fill='x', padx=5, pady=2)

        ttk.Button(btn_frame, text="В сегодня",
                   command=lambda t=task: self.move_to_today(t)).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Редактировать",
                   command=lambda t=task: self.edit_task(t)).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Удалить",
                   command=lambda t=task: self.delete_task(t)).pack(side='right')

    def move_to_today(self, task: Task):
        """Перемещение задачи в сегодняшний день"""
        if self.task_manager:
            task.date_scheduled = self.task_manager.current_date.isoformat()
            self.db.save_task(task)
            self.task_manager.refresh_task_list()
            self.window.destroy()
            messagebox.showinfo("Успех", f"Задача '{task.title}' перемещена в сегодняшние задачи")

    def edit_task(self, task: Task):
        """Редактирование задачи"""
        if self.task_manager:
            dialog = TaskEditDialog(self.window, self.task_manager, task)
            if dialog.result:
                self.window.destroy()
                # Перезапускаем окно бэклога
                BacklogWindow(self.parent, self.db, self.task_manager)

    def delete_task(self, task: Task):
        """Удаление задачи"""
        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
            self.db.delete_task(task.id)
            self.window.destroy()
            # Перезапускаем окно бэклога
            BacklogWindow(self.parent, self.db, self.task_manager)

    def create_backlog_task(self):
        """Создание новой задачи в бэклог"""
        if self.task_manager:
            # Создаем новую задачу с пустой датой (для бэклога)
            new_task = Task()
            new_task.date_scheduled = ""  # Пустая дата означает бэклог
            
            dialog = TaskEditDialog(self.window, self.task_manager, new_task)
            if dialog.result:
                self.window.destroy()
                # Перезапускаем окно бэклога
                BacklogWindow(self.parent, self.db, self.task_manager)