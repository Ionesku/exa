# -*- coding: utf-8 -*-
"""
Task Manager - Виджет списка задач
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .task_models import Task
from .colors import get_priority_color, get_completed_color


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
        self.main_frame.configure(width=280)
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
        canvas = tk.Canvas(parent, bg='white', width=260)
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

        # Закрытие контекстного меню по клику
        canvas.bind('<Button-1>', self.close_context_menu)

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

    def update_tasks(self, tasks):
        """Умное обновление списка задач без полной перерисовки"""
        # Разделяем задачи на активные и выполненные
        active_tasks = [t for t in tasks if not t.is_completed]
        completed_tasks = [t for t in tasks if t.is_completed]
        
        # Обновляем активные задачи
        self._update_tab_tasks(self.active_scrollable_frame, active_tasks)
        
        # Обновляем выполненные задачи
        self._update_tab_tasks(self.completed_scrollable_frame, completed_tasks)
    
    def _update_tab_tasks(self, parent_frame, tasks):
        """Обновление задач в конкретной вкладке"""
        # Очищаем текущие виджеты
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Добавляем новые задачи
        for task in tasks:
            self._create_task_widget(parent_frame, task)
    
    def add_task(self, task: Task):
        """Добавление одной задачи в список"""
        # Определяем родительский фрейм
        if task.is_completed:
            parent_frame = self.completed_scrollable_frame
        else:
            parent_frame = self.active_scrollable_frame
        
        self._create_task_widget(parent_frame, task)
    
    def _create_task_widget(self, parent_frame, task: Task):
        """Создание виджета задачи"""
        # Выбираем цвет для задачи
        if task.is_completed:
            bg_color = get_completed_color()
        else:
            bg_color = get_priority_color(task.priority)

        # Контейнер задачи
        task_frame = tk.Frame(parent_frame,
                             bg=bg_color,
                             relief='solid', bd=1)
        task_frame.pack(fill='x', pady=2)

        # Основная информация
        main_info_frame = tk.Frame(task_frame, bg=bg_color)
        main_info_frame.pack(fill='x', padx=5, pady=(3, 0))

        # Индикатор планирования
        if task.is_planned:
            plan_label = tk.Label(main_info_frame, text="📅",
                                 bg=bg_color,
                                 font=('Arial', 8))
            plan_label.pack(side='right', padx=2)

        # Тип задачи
        task_types = self.task_manager.db.get_task_types()
        task_type = next((t for t in task_types if t.id == task.task_type_id), None)
        type_name = task_type.name if task_type else "Без типа"

        # Название с типом
        title = f"{type_name} / {task.title}"
        if len(title) > 30:
            title = title[:27] + "..."
        
        if task.is_completed:
            title = f"✓ {title}"

        title_label = tk.Label(main_info_frame, text=title,
                              bg=bg_color,
                              fg='white', font=('Arial', 9, 'bold'),
                              anchor='w')
        title_label.pack(fill='x')

        # Дополнительная информация
        info_frame = tk.Frame(task_frame, bg=bg_color)
        info_frame.pack(fill='x', padx=5, pady=(0, 3))

        info_parts = []
        info_parts.append(f"В:{task.importance}")
        info_parts.append(f"С:{task.priority}")
        if task.has_duration:
            info_parts.append(f"Д:{task.duration}м")
        
        info_text = " | ".join(info_parts)
        
        info_label = tk.Label(info_frame, text=info_text,
                             bg=bg_color,
                             fg='white', font=('Arial', 8),
                             anchor='w')
        info_label.pack(fill='x')

        # События
        for widget in [task_frame, main_info_frame, title_label, info_frame, info_label]:
            widget.bind("<Button-1>", lambda e, t=task: self.select_task(t))
            widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))

    def close_context_menu(self, event=None):
        """Закрытие контекстного меню"""
        try:
            self.context_menu.unpost()
        except:
            pass

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def show_context_menu(self, event, task: Task):
        """Показать контекстное меню"""
        self.selected_task = task
        self.task_manager.select_task(task)
        
        # Закрываем меню по любому клику
        self.task_manager.root.bind_all('<Button-1>', self.close_context_menu)
        
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
            self.task_manager.refresh_task_list()