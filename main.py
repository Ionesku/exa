# -*- coding: utf-8 -*-
"""
Task Manager - Система управления задачами
Основной файл приложения
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Callable
import os
import calendar

# Попытка импорта дополнительных модулей (если они существуют)
try:
    from drag_drop_module import DragDropManager, TaskDragDropMixin

    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False


    # Создаем заглушку
    class TaskDragDropMixin:
        def init_drag_drop(self): pass

        def make_task_draggable(self, widget, task): pass

try:
    from calendar_module import CalendarMixin

    CALENDAR_MODULE_AVAILABLE = True
except ImportError:
    CALENDAR_MODULE_AVAILABLE = False


    # Создаем заглушку
    class CalendarMixin:
        def show_calendar(self): pass

# Цветовая схема Material Design (пастельные тона)
COLORS = {
    'quadrant_1': '#E8F5E8',  # Светло-зеленый (Важно и Срочно)
    'quadrant_2': '#E3F2FD',  # Светло-голубой (Важно, не срочно)
    'quadrant_3': '#FFF3E0',  # Светло-оранжевый (Срочно, не важно)
    'quadrant_4': '#F3E5F5',  # Светло-фиолетовый (Не важно, не срочно)
    'inactive': '#F5F5F5',  # Серый для неактивных
    'primary': '#2196F3',  # Основной синий
    'accent': '#FF5722',  # Акцентный оранжевый
    'text': '#212121',  # Основной текст
    'text_secondary': '#757575'  # Вторичный текст
}


@dataclass
class TaskType:
    """Тип задачи"""
    id: int = 0
    name: str = ""
    color: str = "#2196F3"
    description: str = ""


@dataclass
class Task:
    """Класс задачи"""
    id: int = 0
    title: str = ""
    content: str = ""
    importance: int = 1  # 1-10
    duration: int = 30  # минуты
    priority: int = 5  # 1-10 (зеленый к красному)
    task_type_id: int = 1
    is_completed: bool = False
    quadrant: int = 0  # 0-не размещена, 1-4 квадранты
    date_created: str = ""
    date_scheduled: str = ""
    is_recurring: bool = False
    recurrence_pattern: str = ""
    move_count: int = 0  # количество перемещений между квадрантами

    def __post_init__(self):
        if not self.date_created:
            self.date_created = datetime.now().isoformat()


class DatabaseManager:
    """Менеджер базы данных"""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица типов задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#2196F3',
                description TEXT DEFAULT ''
            )
        ''')

        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                importance INTEGER DEFAULT 1,
                duration INTEGER DEFAULT 30,
                priority INTEGER DEFAULT 5,
                task_type_id INTEGER DEFAULT 1,
                is_completed BOOLEAN DEFAULT FALSE,
                quadrant INTEGER DEFAULT 0,
                date_created TEXT NOT NULL,
                date_scheduled TEXT DEFAULT '',
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern TEXT DEFAULT '',
                move_count INTEGER DEFAULT 0,
                FOREIGN KEY (task_type_id) REFERENCES task_types (id)
            )
        ''')

        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Добавляем базовые типы задач если их нет
        cursor.execute('SELECT COUNT(*) FROM task_types')
        if cursor.fetchone()[0] == 0:
            default_types = [
                ('Работа', '#FF5722', 'Рабочие задачи'),
                ('Дом', '#4CAF50', 'Домашние дела'),
                ('Интерес', '#9C27B0', 'Личные интересы'),
                ('Цель', '#FF9800', 'Долгосрочные цели')
            ]
            cursor.executemany(
                'INSERT INTO task_types (name, color, description) VALUES (?, ?, ?)',
                default_types
            )

        conn.commit()
        conn.close()

    def get_tasks(self, date: str = None) -> List[Task]:
        """Получить задачи за определенную дату"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date:
            cursor.execute(
                'SELECT * FROM tasks WHERE date_scheduled = ? OR date_scheduled = ""',
                (date,)
            )
        else:
            cursor.execute('SELECT * FROM tasks')

        rows = cursor.fetchall()
        conn.close()

        tasks = []
        for row in rows:
            task = Task(
                id=row[0], title=row[1], content=row[2], importance=row[3],
                duration=row[4], priority=row[5], task_type_id=row[6],
                is_completed=bool(row[7]), quadrant=row[8], date_created=row[9],
                date_scheduled=row[10], is_recurring=bool(row[11]),
                recurrence_pattern=row[12], move_count=row[13]
            )
            tasks.append(task)

        return tasks

    def save_task(self, task: Task) -> int:
        """Сохранить задачу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if task.id == 0:  # Новая задача
            cursor.execute('''
                INSERT INTO tasks (title, content, importance, duration, priority,
                                 task_type_id, is_completed, quadrant, date_created,
                                 date_scheduled, is_recurring, recurrence_pattern, move_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task.title, task.content, task.importance, task.duration,
                  task.priority, task.task_type_id, task.is_completed,
                  task.quadrant, task.date_created, task.date_scheduled,
                  task.is_recurring, task.recurrence_pattern, task.move_count))
            task_id = cursor.lastrowid
        else:  # Обновление
            cursor.execute('''
                UPDATE tasks SET title=?, content=?, importance=?, duration=?,
                               priority=?, task_type_id=?, is_completed=?,
                               quadrant=?, date_scheduled=?, is_recurring=?,
                               recurrence_pattern=?, move_count=?
                WHERE id=?
            ''', (task.title, task.content, task.importance, task.duration,
                  task.priority, task.task_type_id, task.is_completed,
                  task.quadrant, task.date_scheduled, task.is_recurring,
                  task.recurrence_pattern, task.move_count, task.id))
            task_id = task.id

        conn.commit()
        conn.close()
        return task_id

    def delete_task(self, task_id: int):
        """Удалить задачу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
        conn.close()

    def get_task_types(self) -> List[TaskType]:
        """Получить типы задач"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM task_types')
        rows = cursor.fetchall()
        conn.close()

        return [TaskType(id=row[0], name=row[1], color=row[2], description=row[3])
                for row in rows]

    def save_setting(self, key: str, value: str):
        """Сохранить настройку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str = "") -> str:
        """Получить настройку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default


class TaskManager(TaskDragDropMixin, CalendarMixin):
    """Основной класс приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg='white')

        # Инициализация компонентов
        self.db = DatabaseManager()
        self.current_task: Optional[Task] = None
        self.current_date = datetime.now().date()
        self.day_started = False
        self.day_start_time = None
        self.dragged_task = None  # Для drag&drop

        # Создание интерфейса
        self.setup_ui()

        # Инициализация дополнительных модулей
        if DRAG_DROP_AVAILABLE:
            self.init_drag_drop()

        # Загрузка данных
        self.load_data()

    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка Task Manager
        self.task_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.task_frame, text="Task Manager")
        self.setup_task_manager()

        # Вкладка Аналитика
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Аналитика")
        self.setup_analytics()

        # Пустые вкладки
        for tab_name in ["Питание", "Деньги", "Здоровье"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            ttk.Label(frame, text=f"Вкладка {tab_name} - в разработке",
                      font=('Arial', 14)).pack(expand=True)

        # Горячие клавиши
        self.setup_hotkeys()

    def setup_task_manager(self):
        """Настройка основной вкладки"""
        # Основной контейнер
        main_container = ttk.Frame(self.task_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Верхняя панель с информацией и кнопками
        top_panel = ttk.Frame(main_container)
        top_panel.pack(fill='x', pady=(0, 10))

        # Дата и время
        self.datetime_label = ttk.Label(top_panel, font=('Arial', 12, 'bold'))
        self.datetime_label.pack(side='left')

        # Кнопки управления днем
        self.start_day_btn = ttk.Button(top_panel, text="Начать день",
                                        command=self.start_day)
        self.start_day_btn.pack(side='right', padx=(5, 0))

        self.end_day_btn = ttk.Button(top_panel, text="Завершить день",
                                      command=self.end_day)
        self.end_day_btn.pack(side='right', padx=(5, 0))

        self.calendar_btn = ttk.Button(top_panel, text="Календарь",
                                       command=self.show_calendar)
        self.calendar_btn.pack(side='right', padx=(5, 0))

        self.backlog_btn = ttk.Button(top_panel, text="Бэклог",
                                      command=self.show_backlog)
        self.backlog_btn.pack(side='right', padx=(5, 0))

        # Средняя панель с квадрантами и задачами
        middle_panel = ttk.Frame(main_container)
        middle_panel.pack(fill='both', expand=True)

        # Квадранты (левая часть)
        self.setup_quadrants(middle_panel)

        # Список задач (правая часть)
        self.setup_task_list(middle_panel)

        # Нижняя панель редактирования
        self.setup_edit_panel(main_container)

        # Обновление времени
        self.update_datetime()

    def setup_quadrants(self, parent):
        """Создание области квадрантов"""
        quadrant_frame = ttk.LabelFrame(parent, text="Матрица Эйзенхауэра")
        quadrant_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Создаем сетку 2x2
        self.quadrants = {}

        # Подписи осей
        time_frame = ttk.Frame(quadrant_frame)
        time_frame.pack(fill='x', pady=5)

        self.time_labels = {
            'left': ttk.Label(time_frame, text="9:00", font=('Arial', 10)),
            'top': ttk.Label(time_frame, text="+3ч", font=('Arial', 10)),
            'right': ttk.Label(time_frame, text="+6ч", font=('Arial', 10)),
            'bottom': ttk.Label(time_frame, text="+9ч / 21:00", font=('Arial', 10))
        }

        self.time_labels['left'].pack(side='left')
        self.time_labels['top'].pack()
        self.time_labels['right'].pack(side='right')

        # Основная сетка квадрантов
        grid_frame = ttk.Frame(quadrant_frame)
        grid_frame.pack(fill='both', expand=True)

        quadrant_configs = [
            (0, 0, 1, "Важно и Срочно", COLORS['quadrant_1']),
            (0, 1, 2, "Важно, не срочно", COLORS['quadrant_2']),
            (1, 0, 3, "Срочно, не важно", COLORS['quadrant_3']),
            (1, 1, 4, "Не важно, не срочно", COLORS['quadrant_4'])
        ]

        for row, col, quad_id, title, color in quadrant_configs:
            frame = tk.Frame(grid_frame, bg=color, relief='solid', bd=1)
            frame.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

            # Заголовок квадранта
            ttk.Label(frame, text=title, background=color,
                      font=('Arial', 10, 'bold')).pack(pady=5)

            # Область для задач
            task_area = tk.Frame(frame, bg=color, height=150)
            task_area.pack(fill='both', expand=True, padx=5, pady=5)
            task_area.pack_propagate(False)

            self.quadrants[quad_id] = {
                'frame': frame,
                'task_area': task_area,
                'tasks': []
            }

            # Настройка drag&drop
            self.setup_drop_zone(task_area, quad_id)

        # Настройка пропорций сетки
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        self.time_labels['bottom'].pack(side='bottom')

        # Поле переработок
        overtime_frame = ttk.LabelFrame(quadrant_frame, text="Переработки")
        overtime_frame.pack(fill='x', pady=(10, 0))

        self.overtime_area = tk.Frame(overtime_frame, bg=COLORS['inactive'], height=60)
        self.overtime_area.pack(fill='x', padx=5, pady=5)
        self.overtime_area.pack_propagate(False)

        self.setup_drop_zone(self.overtime_area, 'overtime')

    def setup_task_list(self, parent):
        """Создание списка задач"""
        task_list_frame = ttk.LabelFrame(parent, text="Задачи")
        task_list_frame.pack(side='right', fill='both', expand=True)

        # Кнопка новой задачи сверху
        ttk.Button(task_list_frame, text="+ Новая задача",
                   command=self.create_new_task).pack(fill='x', padx=5, pady=(5, 0))

        # Прокручиваемый список задач
        canvas_frame = ttk.Frame(task_list_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.task_canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical',
                                  command=self.task_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.task_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))
        )

        self.task_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.task_canvas.configure(yscrollcommand=scrollbar.set)

        self.task_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопка новой задачи снизу
        ttk.Button(task_list_frame, text="+ Новая задача",
                   command=self.create_new_task).pack(fill='x', padx=5, pady=(0, 5))

    def setup_edit_panel(self, parent):
        """Создание панели редактирования"""
        edit_frame = ttk.LabelFrame(parent, text="Редактирование задачи")
        edit_frame.pack(fill='x', pady=(10, 0))

        # Основная информация
        info_frame = ttk.Frame(edit_frame)
        info_frame.pack(fill='x', padx=5, pady=5)

        # Название
        ttk.Label(info_frame, text="Название:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(info_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky='ew', padx=(0, 10))

        # Содержание
        ttk.Label(info_frame, text="Содержание:").grid(row=1, column=0, sticky='nw', padx=(0, 5), pady=(5, 0))
        self.content_text = tk.Text(info_frame, height=3, width=40)
        self.content_text.grid(row=1, column=1, columnspan=2, sticky='ew', padx=(0, 10), pady=(5, 0))

        # Параметры
        params_frame = ttk.Frame(edit_frame)
        params_frame.pack(fill='x', padx=5, pady=5)

        # Важность
        ttk.Label(params_frame, text="Важность:").grid(row=0, column=0, sticky='w')
        self.importance_var = tk.IntVar(value=1)
        ttk.Spinbox(params_frame, from_=1, to=10, textvariable=self.importance_var, width=5).grid(row=0, column=1,
                                                                                                  padx=5)

        # Длительность
        ttk.Label(params_frame, text="Длительность (мин):").grid(row=0, column=2, sticky='w', padx=(10, 0))
        self.duration_var = tk.IntVar(value=30)
        ttk.Spinbox(params_frame, from_=5, to=480, increment=15, textvariable=self.duration_var, width=5).grid(row=0,
                                                                                                               column=3,
                                                                                                               padx=5)

        # Приоритет
        ttk.Label(params_frame, text="Приоритет:").grid(row=0, column=4, sticky='w', padx=(10, 0))
        self.priority_var = tk.IntVar(value=5)
        self.priority_scale = ttk.Scale(params_frame, from_=1, to=10, variable=self.priority_var,
                                        orient='horizontal', length=100, command=self.update_priority_color)
        self.priority_scale.grid(row=0, column=5, padx=5)

        self.priority_color_label = tk.Label(params_frame, text="●", font=('Arial', 16), fg=self.get_priority_color(5))
        self.priority_color_label.grid(row=0, column=6, padx=5)

        # Тип задачи
        ttk.Label(params_frame, text="Тип:").grid(row=1, column=0, sticky='w', pady=(5, 0))
        self.task_type_var = tk.StringVar()
        self.task_type_combo = ttk.Combobox(params_frame, textvariable=self.task_type_var, width=15)
        self.task_type_combo.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=(5, 0))

        # Кнопки
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        self.edit_btn = ttk.Button(btn_frame, text="Редактировать", command=self.toggle_edit_mode)
        self.edit_btn.pack(side='left', padx=(0, 5))

        self.save_btn = ttk.Button(btn_frame, text="Сохранить", command=self.save_current_task)
        self.save_btn.pack(side='left', padx=(0, 5))

        self.delete_btn = ttk.Button(btn_frame, text="Удалить", command=self.delete_current_task)
        self.delete_btn.pack(side='left', padx=(0, 5))

        # Изначально поля неактивны
        self.set_edit_mode(False)

    def setup_analytics(self):
        """Настройка вкладки аналитики"""
        ttk.Label(self.analytics_frame, text="Аналитика задач",
                  font=('Arial', 16, 'bold')).pack(pady=10)

        # Список дней с задачами
        self.analytics_tree = ttk.Treeview(self.analytics_frame,
                                           columns=('date', 'completed', 'total_difficulty'),
                                           show='headings')
        self.analytics_tree.heading('date', text='Дата')
        self.analytics_tree.heading('completed', text='Выполнено задач')
        self.analytics_tree.heading('total_difficulty', text='Общая сложность')

        self.analytics_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Кнопка обновления
        ttk.Button(self.analytics_frame, text="Обновить",
                   command=self.update_analytics).pack(pady=5)

    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        self.root.bind('<Control-n>', lambda e: self.create_new_task())
        self.root.bind('<Control-s>', lambda e: self.save_current_task())
        self.root.bind('<Control-d>', lambda e: self.delete_current_task())
        self.root.bind('<F1>', lambda e: self.show_hotkeys())

    def show_hotkeys(self):
        """Показать окно горячих клавиш"""
        hotkey_window = tk.Toplevel(self.root)
        hotkey_window.title("Горячие клавиши")
        hotkey_window.geometry("400x300")

        hotkeys = [
            ("Ctrl+N", "Новая задача"),
            ("Ctrl+S", "Сохранить задачу"),
            ("Ctrl+D", "Удалить задачу"),
            ("F1", "Показать горячие клавиши"),
        ]

        for i, (key, description) in enumerate(hotkeys):
            frame = ttk.Frame(hotkey_window)
            frame.pack(fill='x', padx=10, pady=2)
            ttk.Label(frame, text=key, font=('Arial', 10, 'bold')).pack(side='left')
            ttk.Label(frame, text=description).pack(side='left', padx=(20, 0))

    def setup_drop_zone(self, widget, zone_id):
        """Настройка зоны для перетаскивания (встроенная реализация)"""
        if DRAG_DROP_AVAILABLE:
            return  # Используем продвинутый модуль

        # Простая встроенная реализация drag&drop
        def on_drag_enter(event):
            if hasattr(widget, 'original_bg'):
                return
            widget.original_bg = widget.cget('bg') if hasattr(widget, 'cget') else None
            try:
                widget.config(bg='#E0E0E0')
            except:
                pass

        def on_drag_leave(event):
            if hasattr(widget, 'original_bg') and widget.original_bg:
                try:
                    widget.config(bg=widget.original_bg)
                except:
                    pass

        def on_drop(event):
            if self.dragged_task:
                self.handle_task_drop(self.dragged_task, zone_id)
            if hasattr(widget, 'original_bg') and widget.original_bg:
                try:
                    widget.config(bg=widget.original_bg)
                except:
                    pass

        # Привязка событий
        widget.bind('<Button-1>', on_drop)
        widget.bind('<Enter>', on_drag_enter)
        widget.bind('<Leave>', on_drag_leave)

    def handle_task_drop(self, task: Task, zone_id: str):
        """Обработка сброса задачи в зону"""
        if zone_id.startswith('quadrant_'):
            quadrant = int(zone_id.split('_')[1])
            self.move_task_to_quadrant(task, quadrant)
        elif zone_id == 'overtime':
            self.move_task_to_overtime(task)

    def move_task_to_quadrant(self, task: Task, quadrant: int):
        """Перемещение задачи в квадрант"""
        old_quadrant = task.quadrant
        task.quadrant = quadrant

        if old_quadrant != quadrant:
            task.move_count += 1
            # Увеличиваем важность при каждом перемещении
            task.importance = min(10, task.importance + 1)

        # Сохранение изменений
        self.db.save_task(task)

        # Обновление интерфейса
        self.refresh_task_list()

        # Если это текущая задача, обновляем редактор
        if self.current_task and self.current_task.id == task.id:
            self.current_task = task
            self.load_task_to_editor(task)

        messagebox.showinfo("Успех", f"Задача перемещена в квадрант {quadrant}")

    def move_task_to_overtime(self, task: Task):
        """Перемещение задачи в область переработок"""
        task.quadrant = 5  # Специальное значение для переработок
        task.move_count += 1

        # Сохранение изменений
        self.db.save_task(task)

        # Обновление интерфейса
        self.refresh_task_list()

        messagebox.showinfo("Успех", "Задача перемещена в переработки")

    # Основные методы работы с задачами
    def create_new_task(self):
        """Создание новой задачи"""
        self.current_task = Task()
        self.load_task_to_editor(self.current_task)
        self.set_edit_mode(True)
        self.title_entry.focus()

    def load_task_to_editor(self, task: Task):
        """Загрузка задачи в редактор"""
        self.title_var.set(task.title)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, task.content)
        self.importance_var.set(task.importance)
        self.duration_var.set(task.duration)
        self.priority_var.set(task.priority)
        self.update_priority_color()

        # Загрузка типов задач
        task_types = self.db.get_task_types()
        type_names = [t.name for t in task_types]
        self.task_type_combo['values'] = type_names

        if task.task_type_id and task.task_type_id <= len(task_types):
            self.task_type_var.set(task_types[task.task_type_id - 1].name)
        else:
            self.task_type_var.set(type_names[0] if type_names else "")

    def save_current_task(self):
        """Сохранение текущей задачи"""
        if not self.current_task:
            return

        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название задачи не может быть пустым!")
            return

        # Получение типа задачи
        task_types = self.db.get_task_types()
        type_name = self.task_type_var.get()
        task_type_id = 1
        for i, t in enumerate(task_types):
            if t.name == type_name:
                task_type_id = t.id
                break

        # Обновление данных задачи
        self.current_task.title = self.title_var.get().strip()
        self.current_task.content = self.content_text.get(1.0, tk.END).strip()
        self.current_task.importance = self.importance_var.get()
        self.current_task.duration = self.duration_var.get()
        self.current_task.priority = self.priority_var.get()
        self.current_task.task_type_id = task_type_id

        # Сохранение в БД
        self.current_task.id = self.db.save_task(self.current_task)

        # Обновление интерфейса
        self.refresh_task_list()
        self.set_edit_mode(False)

        messagebox.showinfo("Успех", "Задача сохранена!")

    def delete_current_task(self):
        """Удаление текущей задачи"""
        if not self.current_task or self.current_task.id == 0:
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту задачу?"):
            self.db.delete_task(self.current_task.id)
            self.current_task = None
            self.clear_editor()
            self.refresh_task_list()
            messagebox.showinfo("Успех", "Задача удалена!")

    def clear_editor(self):
        """Очистка редактора"""
        self.title_var.set("")
        self.content_text.delete(1.0, tk.END)
        self.importance_var.set(1)
        self.duration_var.set(30)
        self.priority_var.set(5)
        self.task_type_var.set("")
        self.update_priority_color()
        self.set_edit_mode(False)

    def toggle_edit_mode(self):
        """Переключение режима редактирования"""
        if self.current_task:
            current_mode = str(self.title_entry['state']) != 'disabled'
            self.set_edit_mode(not current_mode)

    def set_edit_mode(self, enabled: bool):
        """Установка режима редактирования"""
        state = 'normal' if enabled else 'disabled'

        self.title_entry.config(state=state)
        self.content_text.config(state=state)

        # Обновление текста кнопки
        if enabled:
            self.edit_btn.config(text="Отменить редактирование")
        else:
            self.edit_btn.config(text="Редактировать")

    def refresh_task_list(self):
        """Обновление списка задач"""
        # Очистка текущего списка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Получение задач за текущую дату
        date_str = self.current_date.isoformat()
        tasks = self.db.get_tasks(date_str)

        # Создание кнопок для задач
        for task in tasks:
            self.create_task_button(task)

        # Обновление квадрантов
        self.refresh_quadrants(tasks)

        # Обновление области переработок
        self.refresh_overtime_area(tasks)

    def create_task_button(self, task: Task):
        """Создание кнопки задачи"""
        task_frame = ttk.Frame(self.scrollable_frame)
        task_frame.pack(fill='x', pady=2)

        # Чекбокс выполнения
        completed_var = tk.BooleanVar(value=task.is_completed)
        completed_check = ttk.Checkbutton(
            task_frame,
            variable=completed_var,
            command=lambda: self.toggle_task_completion(task, completed_var.get())
        )
        completed_check.pack(side='left', padx=(0, 5))

        # Основная кнопка задачи
        task_btn = ttk.Button(
            task_frame,
            text=task.title,
            command=lambda: self.select_task(task)
        )
        task_btn.pack(side='left', fill='x', expand=True)

        # Цветной индикатор приоритета
        priority_color = self.get_priority_color(task.priority)
        priority_label = tk.Label(
            task_frame,
            text="●",
            font=('Arial', 12),
            fg=priority_color
        )
        priority_label.pack(side='right', padx=(5, 0))

        # Настройка drag&drop для задачи
        if DRAG_DROP_AVAILABLE:
            self.make_task_draggable(task_btn, task)
        else:
            # Простая встроенная реализация
            task_btn.bind("<Button-1>", lambda e: self.simple_start_drag(e, task))

        # Tooltip с информацией о задаче
        self.create_tooltip(task_btn, self.get_task_tooltip(task))

    def simple_start_drag(self, event, task: Task):
        """Простое начало перетаскивания"""
        self.dragged_task = task
        self.select_task(task)

        # Визуальная обратная связь
        event.widget.config(relief='sunken')
        self.root.after(100, lambda: event.widget.config(relief='raised'))

    def create_tooltip(self, widget, text):
        """Создание всплывающей подсказки"""

        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=('Arial', 9)
            )
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def get_task_tooltip(self, task: Task) -> str:
        """Получение текста подсказки для задачи"""
        task_types = self.db.get_task_types()
        type_name = "Неизвестно"
        for t in task_types:
            if t.id == task.task_type_id:
                type_name = t.name
                break

        return (f"Название: {task.title}\n"
                f"Тип: {type_name}\n"
                f"Важность: {task.importance}/10\n"
                f"Приоритет: {task.priority}/10\n"
                f"Длительность: {task.duration} мин\n"
                f"Перемещений: {task.move_count}")

    def start_drag(self, event, task: Task):
        """Начало перетаскивания задачи"""
        # Сохраняем информацию о перетаскиваемой задаче
        self.dragged_task = task
        self.select_task(task)

    def select_task(self, task: Task):
        """Выбор задачи для редактирования"""
        self.current_task = task
        self.load_task_to_editor(task)
        self.set_edit_mode(False)

    def toggle_task_completion(self, task: Task, completed: bool):
        """Переключение статуса выполнения задачи"""
        task.is_completed = completed
        self.db.save_task(task)

        # Обновление отображения если это текущая задача
        if self.current_task and self.current_task.id == task.id:
            self.current_task.is_completed = completed

    def refresh_quadrants(self, tasks: List[Task]):
        """Обновление отображения квадрантов"""
        # Очистка квадрантов
        for quad_id in self.quadrants:
            for widget in self.quadrants[quad_id]['task_area'].winfo_children():
                widget.destroy()
            self.quadrants[quad_id]['tasks'] = []

    def refresh_overtime_area(self, tasks: List[Task]):
        """Обновление области переработок"""
        # Очистка области переработок
        for widget in self.overtime_area.winfo_children():
            widget.destroy()

        # Размещение задач переработок
        overtime_tasks = [t for t in tasks if t.quadrant == 5]
        for task in overtime_tasks:
            priority_color = self.get_priority_color(task.priority)
            task_circle = tk.Label(
                self.overtime_area,
                text="●",
                font=('Arial', 12),
                fg=priority_color,
                bg=self.overtime_area['bg']
            )
            task_circle.pack(side='left', padx=2, pady=2)

            # Настройка tooltip
            self.create_tooltip(task_circle, self.get_task_tooltip(task))

            # Настройка перетаскивания
            if DRAG_DROP_AVAILABLE:
                self.make_task_draggable(task_circle, task)
            else:
                task_circle.bind("<Button-1>", lambda e, t=task: self.simple_start_drag(e, t))

            task_circle.bind("<Double-Button-1>", lambda e, t=task: self.select_task(t))

    def add_task_to_quadrant(self, task: Task, quadrant: int):
        """Добавление задачи в квадрант"""
        if quadrant not in self.quadrants:
            return

        task_area = self.quadrants[quadrant]['task_area']

        # Создание индикатора задачи в квадранте
        priority_color = self.get_priority_color(task.priority)
        task_circle = tk.Label(
            task_area,
            text="●",
            font=('Arial', 16),
            fg=priority_color,
            bg=task_area['bg']
        )
        task_circle.pack(side='left', padx=2, pady=2)

        # Настройка tooltip
        self.create_tooltip(task_circle, self.get_task_tooltip(task))

        # Настройка перетаскивания
        if DRAG_DROP_AVAILABLE:
            self.make_task_draggable(task_circle, task)
        else:
            task_circle.bind("<Button-1>", lambda e: self.simple_start_drag(e, task))

        task_circle.bind("<Double-Button-1>", lambda e: self.select_task(task))

        # Сохранение ссылки на задачу
        self.quadrants[quadrant]['tasks'].append(task)

    def start_quadrant_drag(self, event, task: Task):
        """Начало перетаскивания задачи из квадранта"""
        self.dragged_task = task
        # Здесь можно добавить визуальные эффекты перетаскивания

    def get_priority_color(self, priority: int) -> str:
        """Получение цвета для приоритета (градиент от зеленого к красному)"""
        # Интерполяция между зеленым (0, 255, 0) и красным (255, 0, 0)
        ratio = (priority - 1) / 9  # Нормализация к диапазону 0-1

        red = int(255 * ratio)
        green = int(255 * (1 - ratio))

        return f"#{red:02x}{green:02x}00"

    def update_priority_color(self, *args):
        """Обновление цвета индикатора приоритета"""
        priority = int(self.priority_var.get())
        color = self.get_priority_color(priority)
        self.priority_color_label.config(fg=color)

    # Методы управления днем
    def start_day(self):
        """Начало планирования дня"""
        if not self.day_started:
            self.day_started = True
            self.day_start_time = datetime.now().time()

            # Обновление меток времени
            start_hour = self.day_start_time.hour
            self.time_labels['left'].config(text=f"{start_hour}:00")
            self.time_labels['top'].config(text=f"{start_hour + 3}:00")
            self.time_labels['right'].config(text=f"{start_hour + 6}:00")
            self.time_labels['bottom'].config(text=f"{start_hour + 9}:00 / {start_hour + 12}:00")

            self.start_day_btn.config(text="День начат", state='disabled')
            self.end_day_btn.config(state='normal')

            messagebox.showinfo("День начат", f"День начат в {self.day_start_time.strftime('%H:%M')}")

    def end_day(self):
        """Завершение дня"""
        if self.day_started:
            if messagebox.askyesno("Завершение дня", "Завершить текущий день?"):
                self.day_started = False

                # Сохранение времени завершения
                end_time = datetime.now().time()
                self.db.save_setting(f"day_end_{self.current_date.isoformat()}", end_time.isoformat())

                # Переход к следующему дню
                self.current_date += timedelta(days=1)

                # Сброс интерфейса
                self.start_day_btn.config(text="Начать день", state='normal')
                self.end_day_btn.config(state='disabled')

                # Обновление данных
                self.refresh_task_list()

                messagebox.showinfo("День завершен", f"День завершен в {end_time.strftime('%H:%M')}")

    def show_calendar(self):
        """Показать календарь"""
        if CALENDAR_MODULE_AVAILABLE:
            # Используем продвинутый модуль календаря
            super().show_calendar()
        else:
            # Встроенная простая реализация календаря
            self.show_simple_calendar()

    def show_simple_calendar(self):
        """Простая встроенная реализация календаря"""
        calendar_window = tk.Toplevel(self.root)
        calendar_window.title("Календарь")
        calendar_window.geometry("600x400")

        # Заголовок
        ttk.Label(calendar_window, text="Простой календарь",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Текущая дата
        current_date_label = ttk.Label(calendar_window,
                                       text=f"Текущая дата: {self.current_date.strftime('%d.%m.%Y')}")
        current_date_label.pack(pady=5)

        # Поле выбора даты
        date_frame = ttk.Frame(calendar_window)
        date_frame.pack(pady=20)

        ttk.Label(date_frame, text="Выберите дату:").pack(side='left', padx=(0, 10))

        # Простой выбор даты
        self.cal_day_var = tk.StringVar(value=str(self.current_date.day))
        self.cal_month_var = tk.StringVar(value=str(self.current_date.month))
        self.cal_year_var = tk.StringVar(value=str(self.current_date.year))

        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.cal_day_var, width=3).pack(side='left', padx=2)
        ttk.Label(date_frame, text=".").pack(side='left')
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.cal_month_var, width=3).pack(side='left', padx=2)
        ttk.Label(date_frame, text=".").pack(side='left')
        ttk.Spinbox(date_frame, from_=2020, to=2030, textvariable=self.cal_year_var, width=5).pack(side='left', padx=2)

        # Кнопки
        btn_frame = ttk.Frame(calendar_window)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Перейти к дате",
                   command=lambda: self.go_to_selected_date(calendar_window)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Сегодня",
                   command=lambda: self.go_to_today(calendar_window)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Закрыть",
                   command=calendar_window.destroy).pack(side='left', padx=5)

        # Список задач для текущей даты
        tasks_frame = ttk.LabelFrame(calendar_window, text="Задачи на выбранную дату")
        tasks_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.calendar_tasks_list = tk.Listbox(tasks_frame)
        self.calendar_tasks_list.pack(fill='both', expand=True, padx=5, pady=5)

        # Обновление списка задач
        self.update_calendar_tasks()

    def go_to_selected_date(self, window):
        """Переход к выбранной дате"""
        try:
            day = int(self.cal_day_var.get())
            month = int(self.cal_month_var.get())
            year = int(self.cal_year_var.get())

            selected_date = date(year, month, day)
            self.current_date = selected_date
            self.refresh_task_list()
            self.update_calendar_tasks()

            messagebox.showinfo("Успех", f"Переход к дате: {selected_date.strftime('%d.%m.%Y')}")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверная дата!")

    def go_to_today(self, window):
        """Переход к сегодняшней дате"""
        self.current_date = date.today()
        self.refresh_task_list()
        self.update_calendar_tasks()

        # Обновление полей
        self.cal_day_var.set(str(self.current_date.day))
        self.cal_month_var.set(str(self.current_date.month))
        self.cal_year_var.set(str(self.current_date.year))

    def update_calendar_tasks(self):
        """Обновление списка задач в календаре"""
        if not hasattr(self, 'calendar_tasks_list'):
            return

        self.calendar_tasks_list.delete(0, tk.END)

        date_str = self.current_date.isoformat()
        tasks = self.db.get_tasks(date_str)

        if not tasks:
            self.calendar_tasks_list.insert(tk.END, "Нет задач на эту дату")
        else:
            for task in tasks:
                status = "✓" if task.is_completed else "○"
                self.calendar_tasks_list.insert(tk.END, f"{status} {task.title}")

    def create_new_task_for_date(self, target_date: date):
        """Создание новой задачи для указанной даты"""
        new_task = Task()
        new_task.date_scheduled = target_date.isoformat()
        new_task.title = f"Новая задача на {target_date.strftime('%d.%m.%Y')}"

        # Сохранение задачи
        new_task.id = self.db.save_task(new_task)

        return new_task

    def show_backlog(self):
        """Показать бэклог"""
        backlog_window = tk.Toplevel(self.root)
        backlog_window.title("Бэклог задач")
        backlog_window.geometry("600x400")

        # Список всех задач без даты
        ttk.Label(backlog_window, text="Бэклог задач",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Получение задач без установленной даты
        all_tasks = self.db.get_tasks()
        backlog_tasks = [t for t in all_tasks if not t.date_scheduled]

        if not backlog_tasks:
            ttk.Label(backlog_window, text="Нет задач в бэклоге").pack(expand=True)
            return

        # Список задач
        backlog_frame = ttk.Frame(backlog_window)
        backlog_frame.pack(fill='both', expand=True, padx=10, pady=10)

        for task in backlog_tasks:
            task_frame = ttk.Frame(backlog_frame)
            task_frame.pack(fill='x', pady=2)

            ttk.Button(
                task_frame,
                text=task.title,
                command=lambda t=task: self.move_to_today(t, backlog_window)
            ).pack(side='left', fill='x', expand=True)

            ttk.Button(
                task_frame,
                text="Удалить",
                command=lambda t=task: self.delete_from_backlog(t, backlog_window)
            ).pack(side='right', padx=(5, 0))

    def move_to_today(self, task: Task, parent_window):
        """Перемещение задачи в сегодняшний день"""
        task.date_scheduled = self.current_date.isoformat()
        self.db.save_task(task)
        self.refresh_task_list()
        parent_window.destroy()
        messagebox.showinfo("Успех", f"Задача '{task.title}' перемещена в сегодняшние задачи")

    def delete_from_backlog(self, task: Task, parent_window):
        """Удаление задачи из бэклога"""
        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
            self.db.delete_task(task.id)
            parent_window.destroy()
            self.show_backlog()  # Обновление окна бэклога

    def update_analytics(self):
        """Обновление аналитики"""
        # Очистка дерева
        for item in self.analytics_tree.get_children():
            self.analytics_tree.delete(item)

        # Получение всех задач
        all_tasks = self.db.get_tasks()

        # Группировка по датам
        days_data = {}
        for task in all_tasks:
            if task.date_scheduled:
                date = task.date_scheduled
                if date not in days_data:
                    days_data[date] = {'completed': 0, 'total_difficulty': 0}

                if task.is_completed:
                    days_data[date]['completed'] += 1
                    days_data[date]['total_difficulty'] += task.importance

        # Заполнение дерева
        for date, data in sorted(days_data.items(), reverse=True):
            self.analytics_tree.insert('', 'end', values=(
                date,
                data['completed'],
                data['total_difficulty']
            ))

    def update_datetime(self):
        """Обновление отображения даты и времени"""
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%H:%M:%S")
        self.datetime_label.config(text=f"{date_str} | {time_str}")

        # Обновление каждую секунду
        self.root.after(1000, self.update_datetime)

    def load_data(self):
        """Загрузка данных при запуске"""
        self.refresh_task_list()
        self.update_analytics()

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


def main():
    """Точка входа в приложение"""
    try:
        app = TaskManager()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()