# -*- coding: utf-8 -*-
"""
Task Manager - Окно бэклога с улучшенной прокруткой
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

from .task_models import Task
from .task_edit_dialog import TaskEditDialog
from .utils import TaskUtils, DateUtils, truncate_text
from .colors import get_priority_color


class BacklogWindow:
    """Окно для управления бэклогом задач"""

    def __init__(self, parent, db_manager, task_manager):
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager
        self.selected_task = None
        self.task_groups = {}

        # Создание окна
        self.window = tk.Toplevel(parent)
        self.window.title("Бэклог задач")
        self.window.geometry("800x600")
        self.window.transient(parent)

        self.setup_ui()
        self.setup_context_menu()
        self.load_backlog_tasks()

    def setup_ui(self):
        """Создание интерфейса окна бэклога с прокруткой"""
        # Верхняя панель
        top_frame = ttk.Frame(self.window)
        top_frame.pack(fill='x', padx=10, pady=(10, 5))

        ttk.Label(top_frame, text="Бэклог задач", 
                  font=('Arial', 14, 'bold')).pack(side='left')

        ttk.Button(top_frame, text="Обновить",
                   command=self.load_backlog_tasks).pack(side='right', padx=(5, 0))

        ttk.Button(top_frame, text="Новая задача",
                   command=self.create_new_task).pack(side='right')

        # Фрейм для прокрутки
        scroll_frame = tk.Frame(self.window)
        scroll_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))

        # Canvas для прокрутки
        self.canvas = tk.Canvas(scroll_frame, bg='white', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(scroll_frame, orient='vertical', command=self.canvas.yview)

        # Контейнер для групп
        self.groups_container = ttk.Frame(self.canvas)
        
        # Окно в canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.groups_container, anchor="nw")
        
        # Настройка прокрутки
        self.groups_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Размещение
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Динамическое отображение scrollbar
        def check_scrollbar(event=None):
            self.canvas.update_idletasks()
            if self.groups_container.winfo_reqheight() > self.canvas.winfo_height():
                if not self.scrollbar.winfo_manager():
                    self.scrollbar.pack(side="right", fill="y")
            else:
                if self.scrollbar.winfo_manager():
                    self.scrollbar.pack_forget()
        
        self.groups_container.bind("<Configure>", check_scrollbar)
        self.canvas.bind("<Configure>", check_scrollbar)
        
        # Прокрутка колесом мыши
        def _on_mousewheel(event):
            if self.groups_container.winfo_reqheight() > self.canvas.winfo_height():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_enter(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
            self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux up
            self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))  # Linux down
        
        def _on_leave(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        
        self.canvas.bind("<Enter>", _on_enter)
        self.canvas.bind("<Leave>", _on_leave)

        # Статус бар
        self.status_label = ttk.Label(self.window, text="", relief='sunken')
        self.status_label.pack(fill='x', side='bottom')

    def setup_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Переместить на сегодня",
                                      command=self.move_to_today)
        self.context_menu.add_command(label="Переместить на дату...",
                                      command=self.move_to_date)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать",
                                      command=self.edit_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить",
                                      command=self.delete_task)

    def load_backlog_tasks(self):
        """Загрузка задач из бэклога"""
        # Очистка текущего содержимого
        for widget in self.groups_container.winfo_children():
            widget.destroy()

        # Получение задач из бэклога
        tasks = self.db.get_tasks(include_backlog=True)
        backlog_tasks = [t for t in tasks if not t.date_scheduled]

        if not backlog_tasks:
            # Показываем сообщение о пустом бэклоге
            empty_label = ttk.Label(self.groups_container,
                                    text="Бэклог пуст",
                                    font=('Arial', 12))
            empty_label.pack(expand=True, pady=50)
            self.update_status(0)
            return

        # Группировка задач
        task_types = self.db.get_task_types()
        grouped_tasks = TaskUtils.group_tasks_by_type(backlog_tasks, task_types)

        # Создание групп
        for type_name, tasks in grouped_tasks.items():
            self.create_group(type_name, tasks)

        self.update_status(len(backlog_tasks))

    def create_group(self, type_name: str, tasks: List[Task]):
        """Создание группы задач"""
        # Фрейм группы
        group_frame = ttk.LabelFrame(self.groups_container,
                                     text=f"{type_name} ({len(tasks)})")
        group_frame.pack(fill='x', pady=5)

        # Контейнер для задач
        tasks_frame = ttk.Frame(group_frame)
        tasks_frame.pack(fill='x', padx=5, pady=5)

        # Создание виджетов задач
        for task in tasks:
            self.create_task_widget(tasks_frame, task)

    def create_task_widget(self, parent_frame, task: Task):
        """Создание виджета для одной задачи"""
        # Фрейм задачи
        task_frame = tk.Frame(parent_frame,
                              bg=get_priority_color(task.priority),
                              relief='raised', bd=1,
                              cursor='hand2')
        task_frame.pack(fill='x', pady=2)

        # Информация о задаче
        info_frame = tk.Frame(task_frame, bg=task_frame['bg'])
        info_frame.pack(fill='x', padx=5, pady=3)

        # Название
        title_label = tk.Label(info_frame,
                               text=truncate_text(task.title, 50),
                               bg=task_frame['bg'],
                               fg='white',
                               font=('Arial', 10, 'bold'),
                               anchor='w')
        title_label.pack(fill='x')

        # Дополнительная информация
        info_text = f"Важность: {task.importance} | Срочность: {task.priority}"
        if task.has_duration:
            info_text += f" | Длительность: {task.duration}м"

        detail_label = tk.Label(info_frame,
                                text=info_text,
                                bg=task_frame['bg'],
                                fg='white',
                                font=('Arial', 8),
                                anchor='w')
        detail_label.pack(fill='x')

        # События
        task_frame.bind("<Button-1>", lambda e: self.select_task(task))
        task_frame.bind("<Double-Button-1>", lambda e: self.move_to_today())
        task_frame.bind("<Button-3>", lambda e: self.show_context_menu(e, task))

        title_label.bind("<Button-1>", lambda e: self.select_task(task))
        title_label.bind("<Double-Button-1>", lambda e: self.move_to_today())
        title_label.bind("<Button-3>", lambda e: self.show_context_menu(e, task))

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task

    def show_context_menu(self, event, task: Task):
        """Показ контекстного меню"""
        self.selected_task = task
        self.context_menu.post(event.x_root, event.y_root)

    def move_to_today(self):
        """Перемещение задачи на сегодня"""
        if not self.selected_task:
            return

        self.selected_task.date_scheduled = DateUtils.today_iso()
        self.db.save_task(self.selected_task)

        self.load_backlog_tasks()
        if hasattr(self.task_manager, 'refresh_task_list'):
            self.task_manager.refresh_task_list()

        messagebox.showinfo("Успех",
                            f"Задача '{self.selected_task.title}' перемещена на сегодня")

    def move_to_date(self):
        """Перемещение задачи на выбранную дату"""
        if not self.selected_task:
            return

        # Создаем диалог выбора даты
        date_dialog = tk.Toplevel(self.window)
        date_dialog.title("Выбор даты")
        date_dialog.geometry("300x150")
        date_dialog.transient(self.window)

        ttk.Label(date_dialog, text="Выберите дату:").pack(pady=10)

        # Календарь или простое поле ввода
        date_var = tk.StringVar(value=DateUtils.today_str())
        date_entry = ttk.Entry(date_dialog, textvariable=date_var)
        date_entry.pack(pady=5)

        ttk.Label(date_dialog, text="Формат: ДД.ММ.ГГГГ",
                  font=('Arial', 8)).pack()

        def save_date():
            try:
                date_str = date_var.get()
                # Преобразуем в ISO формат
                date_iso = DateUtils.to_iso_format(date_str)
                
                self.selected_task.date_scheduled = date_iso
                self.db.save_task(self.selected_task)

                date_dialog.destroy()
                self.load_backlog_tasks()
                
                if hasattr(self.task_manager, 'refresh_task_list'):
                    self.task_manager.refresh_task_list()

                messagebox.showinfo("Успех",
                                    f"Задача перемещена на {date_str}")
            except Exception as e:
                messagebox.showerror("Ошибка",
                                     f"Неверный формат даты: {str(e)}")

        ttk.Button(date_dialog, text="Сохранить",
                   command=save_date).pack(pady=10)

        date_dialog.grab_set()

    def edit_task(self):
        """Редактирование задачи"""
        if not self.selected_task:
            return

        dialog = TaskEditDialog(self.window, self.task_manager, self.selected_task)
        if dialog.result:
            self.load_backlog_tasks()

    def delete_task(self):
        """Удаление задачи"""
        if not self.selected_task:
            return

        if messagebox.askyesno("Подтверждение",
                               f"Удалить задачу '{self.selected_task.title}'?"):
            self.db.delete_task(self.selected_task.id)
            self.load_backlog_tasks()
            messagebox.showinfo("Успех", "Задача удалена")

    def create_new_task(self):
        """Создание новой задачи в бэклоге"""
        # Создаем задачу без даты
        task = Task()
        task.date_scheduled = ""  # Пустая дата = бэклог
        
        dialog = TaskEditDialog(self.window, self.task_manager, task)
        if dialog.result:
            self.load_backlog_tasks()

    def update_status(self, count: int):
        """Обновление статусной строки"""
        self.status_label.config(text=f"Всего задач в бэклоге: {count}")