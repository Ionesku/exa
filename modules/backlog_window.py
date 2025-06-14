# -*- coding: utf-8 -*-
"""
Task Manager - Оптимизированное окно бэклога (исправленная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .task_models import Task
from .task_edit_dialog import TaskEditDialog
from .colors import get_priority_color, get_completed_color, UI_COLORS
from .utils import TaskUtils, truncate_text

logger = logging.getLogger(__name__)


class BacklogWindow:
    """Оптимизированное окно бэклога с эффективным использованием пространства"""

    def __init__(self, parent, db_manager, task_manager):
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager
        self.selected_task: Optional[Task] = None
        self.current_filter = "all"
        self.search_var = tk.StringVar()
        
        # Кеш для задач
        self.all_tasks: List[Task] = []
        self.filtered_tasks: List[Task] = []
        
        # Маппинг item -> task_id для Treeview
        self.item_to_task_id = {}
        
        # Создание окна
        self.window = tk.Toplevel(parent)
        self.window.title("Бэклог задач")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        """Создание оптимизированного интерфейса"""
        # Главный контейнер
        main_container = ttk.PanedWindow(self.window, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Левая панель - фильтры и группы
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        self.setup_left_panel(left_panel)
        
        # Правая панель - список задач
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=3)
        self.setup_right_panel(right_panel)
        
        # Установка начальных пропорций (250 пикселей для левой панели)
        self.window.update()
        main_container.sashpos(0, 250)
        
        # Нижняя панель - статус и кнопки
        bottom_panel = ttk.Frame(self.window)
        bottom_panel.pack(fill='x', side='bottom', padx=5, pady=(0, 5))
        self.setup_bottom_panel(bottom_panel)

    def setup_left_panel(self, parent):
        """Настройка левой панели с фильтрами"""
        # Заголовок
        ttk.Label(parent, text="Фильтры", font=('Arial', 12, 'bold')).pack(pady=(5, 10))
        
        # Поиск
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill='x', padx=5, pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").pack(anchor='w')
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill='x', pady=2)
        search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        
        # Разделитель
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Группы по типам
        ttk.Label(parent, text="Типы задач", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        
        # Фрейм для типов с прокруткой
        types_frame = ttk.Frame(parent)
        types_frame.pack(fill='both', expand=True, padx=5)
        
        # Canvas для прокрутки типов
        self.types_canvas = tk.Canvas(types_frame, bg='white', highlightthickness=0)
        types_scrollbar = ttk.Scrollbar(types_frame, orient='vertical', command=self.types_canvas.yview)
        
        self.types_list_frame = ttk.Frame(self.types_canvas)
        self.types_canvas_window = self.types_canvas.create_window((0, 0), window=self.types_list_frame, anchor="nw")
        
        self.types_list_frame.bind('<Configure>', 
            lambda e: self.types_canvas.configure(scrollregion=self.types_canvas.bbox("all")))
        
        self.types_canvas.bind('<Configure>',
            lambda e: self.types_canvas.itemconfig(self.types_canvas_window, width=e.width))
        
        self.types_canvas.configure(yscrollcommand=types_scrollbar.set)
        
        self.types_canvas.pack(side="left", fill="both", expand=True)
        types_scrollbar.pack(side="right", fill="y")
        
        # Кнопки управления
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(buttons_frame, text="Все задачи", 
                  command=lambda: self.filter_by_type("all")).pack(fill='x', pady=2)
        
        ttk.Button(buttons_frame, text="Без типа",
                  command=lambda: self.filter_by_type(None)).pack(fill='x', pady=2)

    def setup_right_panel(self, parent):
        """Настройка правой панели со списком задач"""
        # Верхняя панель с информацией
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        self.tasks_info_label = ttk.Label(top_frame, text="Всего задач: 0", 
                                         font=('Arial', 10, 'bold'))
        self.tasks_info_label.pack(side='left')
        
        # Кнопки сортировки
        sort_frame = ttk.Frame(top_frame)
        sort_frame.pack(side='right')
        
        ttk.Label(sort_frame, text="Сортировка:").pack(side='left', padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="priority")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                 values=["priority", "importance", "title", "type"],
                                 state='readonly', width=15)
        sort_combo.pack(side='left')
        sort_combo.bind('<<ComboboxSelected>>', lambda e: self.sort_tasks())
        
        # Список задач с использованием Treeview для компактности
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Создаем Treeview (без task_id в columns)
        columns = ('type', 'importance', 'priority', 'duration')
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=20)
        
        # Настройка колонок
        self.tasks_tree.heading('#0', text='Задача')
        self.tasks_tree.heading('type', text='Тип')
        self.tasks_tree.heading('importance', text='В')
        self.tasks_tree.heading('priority', text='С')
        self.tasks_tree.heading('duration', text='Время')
        
        # Ширина колонок
        self.tasks_tree.column('#0', width=400, stretch=True)
        self.tasks_tree.column('type', width=120)
        self.tasks_tree.column('importance', width=50, anchor='center')
        self.tasks_tree.column('priority', width=50, anchor='center')
        self.tasks_tree.column('duration', width=70, anchor='center')
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.tasks_tree.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient='horizontal', command=self.tasks_tree.xview)
        self.tasks_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Размещение
        self.tasks_tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # События
        self.tasks_tree.bind('<Double-Button-1>', lambda e: self.move_to_today())
        self.tasks_tree.bind('<Button-3>', self.show_context_menu)
        self.tasks_tree.bind('<<TreeviewSelect>>', self.on_task_select)
        
        # Создаем теги для цветов
        for i in range(1, 11):
            color = get_priority_color(i)
            self.tasks_tree.tag_configure(f'priority_{i}', foreground=color)
        
        # Контекстное меню
        self.setup_context_menu()

    def setup_bottom_panel(self, parent):
        """Настройка нижней панели"""
        # Левая часть - статус
        self.status_label = ttk.Label(parent, text="", font=('Arial', 9))
        self.status_label.pack(side='left')
        
        # Правая часть - кнопки
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(side='right')
        
        ttk.Button(buttons_frame, text="Новая задача",
                  command=self.create_new_task).pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="На сегодня",
                  command=self.move_to_today).pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="Редактировать",
                  command=self.edit_task).pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="Удалить",
                  command=self.delete_task).pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="Обновить",
                  command=self.load_tasks).pack(side='left', padx=2)

    def setup_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Переместить на сегодня",
                                     command=self.move_to_today)
        self.context_menu.add_command(label="Переместить на завтра",
                                     command=self.move_to_tomorrow)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать",
                                     command=self.edit_task)
        self.context_menu.add_command(label="Дублировать",
                                     command=self.duplicate_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить",
                                     command=self.delete_task)

    def load_tasks(self):
        """Загрузка всех задач из бэклога"""
        # Получаем все задачи
        all_tasks = self.db.get_tasks(include_backlog=True)
        self.all_tasks = [t for t in all_tasks if not t.date_scheduled]
        
        # Обновляем список типов
        self.update_types_list()
        
        # Применяем фильтры
        self.apply_filters()

    def update_types_list(self):
        """Обновление списка типов в левой панели"""
        # Очищаем текущий список
        for widget in self.types_list_frame.winfo_children():
            widget.destroy()
        
        # Получаем типы и считаем задачи
        task_types = self.db.get_task_types()
        type_counts = {}
        
        for task in self.all_tasks:
            type_id = task.task_type_id
            if type_id in type_counts:
                type_counts[type_id] += 1
            else:
                type_counts[type_id] = 1
        
        # Создаем кнопки для каждого типа
        for i, task_type in enumerate(task_types):
            count = type_counts.get(task_type.id, 0)
            if count > 0:
                # Фрейм для типа
                type_frame = tk.Frame(self.types_list_frame, bg='white')
                type_frame.pack(fill='x', pady=0)
                
                # Кнопка с типом
                btn_frame = tk.Frame(type_frame, bg='white')
                btn_frame.pack(fill='x', pady=1)
                
                # Цветной индикатор
                color_label = tk.Label(btn_frame, text="●", fg=task_type.color,
                                      font=('Arial', 12), bg='white')
                color_label.pack(side='left', padx=(5, 0))
                
                # Кнопка с названием и количеством
                btn = tk.Button(btn_frame, 
                               text=f"{task_type.name} ({count})",
                               relief='flat',
                               bg='white',
                               anchor='w',
                               bd=0,
                               padx=10,
                               pady=5,
                               command=lambda t=task_type: self.filter_by_type(t))
                btn.pack(side='left', fill='x', expand=True)
                
                # Подсветка при наведении
                def on_enter(e, button=btn):
                    button.config(bg='#E3F2FD')
                
                def on_leave(e, button=btn):
                    button.config(bg='white')
                
                btn.bind('<Enter>', on_enter)
                btn.bind('<Leave>', on_leave)
                
                # Разделитель (кроме последнего)
                if i < len(task_types) - 1:
                    separator = tk.Frame(self.types_list_frame, height=1, bg='#E0E0E0')
                    separator.pack(fill='x', padx=10)

    def filter_by_type(self, task_type):
        """Фильтрация по типу задачи"""
        if task_type == "all":
            self.current_filter = "all"
        elif task_type is None:
            self.current_filter = None
        else:
            self.current_filter = task_type.id
        
        self.apply_filters()

    def apply_filters(self):
        """Применение всех фильтров"""
        # Начинаем со всех задач
        self.filtered_tasks = self.all_tasks.copy()
        
        # Фильтр по типу
        if self.current_filter != "all":
            if self.current_filter is None:
                self.filtered_tasks = [t for t in self.filtered_tasks if t.task_type_id == 0]
            else:
                self.filtered_tasks = [t for t in self.filtered_tasks if t.task_type_id == self.current_filter]
        
        # Фильтр по поиску
        search_text = self.search_var.get().lower()
        if search_text:
            self.filtered_tasks = [t for t in self.filtered_tasks 
                                 if search_text in t.title.lower() or 
                                    search_text in t.content.lower()]
        
        # Сортировка
        self.sort_tasks()
        
        # Обновляем отображение
        self.update_tasks_display()

    def sort_tasks(self):
        """Сортировка задач"""
        sort_by = self.sort_var.get()
        
        if sort_by == "priority":
            self.filtered_tasks.sort(key=lambda t: t.priority, reverse=True)
        elif sort_by == "importance":
            self.filtered_tasks.sort(key=lambda t: t.importance, reverse=True)
        elif sort_by == "title":
            self.filtered_tasks.sort(key=lambda t: t.title.lower())
        elif sort_by == "type":
            self.filtered_tasks.sort(key=lambda t: t.task_type_id)

    def update_tasks_display(self):
        """Обновление отображения задач в дереве"""
        # Очищаем дерево и маппинг
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        self.item_to_task_id.clear()
        
        # Получаем типы для отображения
        task_types = {t.id: t for t in self.db.get_task_types()}
        
        # Добавляем задачи
        for task in self.filtered_tasks:
            # Определяем тип
            task_type = task_types.get(task.task_type_id)
            type_name = task_type.name if task_type else "Без типа"
            
            # Длительность
            duration = f"{task.duration}м" if task.has_duration else "-"
            
            # Вставляем в дерево
            item = self.tasks_tree.insert('', 'end',
                                        text=task.title,
                                        values=(type_name, task.importance, task.priority, duration),
                                        tags=(f'priority_{task.priority}',))
            
            # Сохраняем маппинг
            self.item_to_task_id[item] = task.id
        
        # Обновляем информацию
        self.tasks_info_label.config(text=f"Показано задач: {len(self.filtered_tasks)} из {len(self.all_tasks)}")
        self.update_status()

    def on_task_select(self, event):
        """Обработка выбора задачи"""
        selection = self.tasks_tree.selection()
        if selection:
            item = selection[0]
            task_id = self.item_to_task_id.get(item)
            if task_id:
                self.selected_task = next((t for t in self.all_tasks if t.id == task_id), None)
                self.update_status()

    def show_context_menu(self, event):
        """Показ контекстного меню"""
        # Выбираем элемент под курсором
        item = self.tasks_tree.identify_row(event.y)
        if item:
            self.tasks_tree.selection_set(item)
            self.on_task_select(None)
            self.context_menu.post(event.x_root, event.y_root)

    def move_to_today(self):
        """Перемещение задачи на сегодня"""
        if not self.selected_task:
            messagebox.showwarning("Предупреждение", "Выберите задачу для перемещения")
            return
        
        self.selected_task.date_scheduled = datetime.now().date().isoformat()
        self.db.save_task(self.selected_task)
        
        # Удаляем из списка
        self.all_tasks.remove(self.selected_task)
        self.apply_filters()
        
        # Обновляем основное окно
        self.task_manager.refresh_ui()
        
        messagebox.showinfo("Успех", f"Задача '{self.selected_task.title}' перемещена на сегодня")

    def move_to_tomorrow(self):
        """Перемещение задачи на завтра"""
        if not self.selected_task:
            return
        
        from datetime import timedelta
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        
        self.selected_task.date_scheduled = tomorrow
        self.db.save_task(self.selected_task)
        
        self.all_tasks.remove(self.selected_task)
        self.apply_filters()
        
        messagebox.showinfo("Успех", f"Задача '{self.selected_task.title}' перемещена на завтра")

    def edit_task(self):
        """Редактирование задачи"""
        if not self.selected_task:
            messagebox.showwarning("Предупреждение", "Выберите задачу для редактирования")
            return
        
        dialog = TaskEditDialog(self.window, self.task_manager, self.selected_task)
        if dialog.result:
            self.load_tasks()

    def duplicate_task(self):
        """Дублирование задачи"""
        if not self.selected_task:
            return
        
        # Создаем копию
        new_task = Task(
            title=f"{self.selected_task.title} (копия)",
            content=self.selected_task.content,
            importance=self.selected_task.importance,
            priority=self.selected_task.priority,
            task_type_id=self.selected_task.task_type_id,
            has_duration=self.selected_task.has_duration,
            duration=self.selected_task.duration,
            date_scheduled=""  # В бэклог
        )
        
        self.db.save_task(new_task)
        self.load_tasks()
        
        messagebox.showinfo("Успех", "Задача продублирована")

    def delete_task(self):
        """Удаление задачи"""
        if not self.selected_task:
            messagebox.showwarning("Предупреждение", "Выберите задачу для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", 
                              f"Удалить задачу '{self.selected_task.title}'?"):
            self.db.delete_task(self.selected_task.id)
            self.all_tasks.remove(self.selected_task)
            self.selected_task = None
            self.apply_filters()

    def create_new_task(self):
        """Создание новой задачи в бэклоге"""
        new_task = Task()
        new_task.date_scheduled = ""  # Пустая дата = бэклог
        
        dialog = TaskEditDialog(self.window, self.task_manager, new_task)
        if dialog.result:
            self.load_tasks()

    def update_status(self):
        """Обновление статусной строки"""
        if self.selected_task:
            task_types = {t.id: t for t in self.db.get_task_types()}
            task_type = task_types.get(self.selected_task.task_type_id)
            type_name = task_type.name if task_type else "Без типа"
            
            status = f"Выбрана: {truncate_text(self.selected_task.title, 30)} | "
            status += f"Тип: {type_name} | "
            status += f"В: {self.selected_task.importance} | С: {self.selected_task.priority}"
            
            self.status_label.config(text=status)
        else:
            self.status_label.config(text=f"Всего задач в бэклоге: {len(self.all_tasks)}")