# -*- coding: utf-8 -*-
"""
Task Manager - Модуль календаря
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date, timedelta
from typing import Dict, List, Callable, Optional


class CalendarWidget:
    """Виджет календаря для выбора дат и навигации"""

    def __init__(self, parent: tk.Widget, on_date_select: Callable[[date], None] = None,
                 get_tasks_for_date: Callable[[date], List] = None):
        self.parent = parent
        self.on_date_select = on_date_select
        self.get_tasks_for_date = get_tasks_for_date

        self.current_date = date.today()
        self.selected_date = date.today()

        self.setup_calendar()
        self.update_calendar()

    def setup_calendar(self):
        """Создание интерфейса календаря"""
        # Основной фрейм
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Заголовок с навигацией
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 10))

        # Кнопки навигации
        ttk.Button(header_frame, text="<<",
                   command=self.prev_year, width=3).pack(side='left')
        ttk.Button(header_frame, text="<",
                   command=self.prev_month, width=3).pack(side='left', padx=(5, 0))

        # Текущий месяц и год
        self.month_year_label = ttk.Label(header_frame, font=('Arial', 14, 'bold'))
        self.month_year_label.pack(side='left', expand=True)

        ttk.Button(header_frame, text=">",
                   command=self.next_month, width=3).pack(side='right', padx=(0, 5))
        ttk.Button(header_frame, text=">>",
                   command=self.next_year, width=3).pack(side='right')

        # Кнопка "Сегодня"
        ttk.Button(header_frame, text="Сегодня",
                   command=self.go_to_today).pack(side='right', padx=(0, 10))

        # Сетка календаря
        self.calendar_frame = ttk.Frame(self.main_frame)
        self.calendar_frame.pack(fill='both', expand=True)

        # Заголовки дней недели
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            label = ttk.Label(self.calendar_frame, text=day,
                              font=('Arial', 10, 'bold'), anchor='center')
            label.grid(row=0, column=i, sticky='ew', padx=1, pady=1)

        # Настройка пропорций колонок
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)

        # Массив для хранения кнопок дней
        self.day_buttons = {}

    def prev_month(self):
        """Переход к предыдущему месяцу"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()

    def next_month(self):
        """Переход к следующему месяцу"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()

    def prev_year(self):
        """Переход к предыдущему году"""
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self.update_calendar()

    def next_year(self):
        """Переход к следующему году"""
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self.update_calendar()

    def go_to_today(self):
        """Переход к текущей дате"""
        self.current_date = date.today()
        self.selected_date = date.today()
        self.update_calendar()
        if self.on_date_select:
            self.on_date_select(self.selected_date)

    def update_calendar(self):
        """Обновление отображения календаря"""
        # Обновление заголовка
        month_names = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_name = month_names[self.current_date.month - 1]
        self.month_year_label.config(text=f"{month_name} {self.current_date.year}")

        # Очистка старых кнопок
        for button in self.day_buttons.values():
            button.destroy()
        self.day_buttons.clear()

        # Получение календаря месяца
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)

        # Создание кнопок для дней
        for week_num, week in enumerate(cal, start=1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue

                day_date = date(self.current_date.year, self.current_date.month, day)

                # Определение стиля кнопки
                style_config = self.get_day_style(day_date)

                # Создание кнопки дня
                day_btn = tk.Button(
                    self.calendar_frame,
                    text=str(day),
                    command=lambda d=day_date: self.select_date(d),
                    **style_config
                )
                day_btn.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)

                # Добавление информации о задачах
                if self.get_tasks_for_date:
                    tasks = self.get_tasks_for_date(day_date)
                    if tasks:
                        task_count = len(tasks)
                        completed_count = sum(1 for t in tasks if t.is_completed)

                        # Добавление индикатора количества задач
                        info_text = f"{day}\n({completed_count}/{task_count})"
                        day_btn.config(text=info_text, font=('Arial', 8))

                self.day_buttons[day_date] = day_btn

        # Настройка пропорций строк
        for i in range(len(cal) + 1):
            self.calendar_frame.grid_rowconfigure(i, weight=1)

    def get_day_style(self, day_date: date) -> Dict:
        """Получение стиля для дня календаря"""
        today = date.today()

        style = {
            'relief': 'raised',
            'bd': 1,
            'font': ('Arial', 10),
            'width': 8,
            'height': 3
        }

        # Сегодняшний день
        if day_date == today:
            style.update({
                'bg': '#2196F3',
                'fg': 'white',
                'font': ('Arial', 10, 'bold')
            })
        # Выбранная дата
        elif day_date == self.selected_date:
            style.update({
                'bg': '#FFC107',
                'fg': 'black',
                'font': ('Arial', 10, 'bold')
            })
        # Выходные дни
        elif day_date.weekday() >= 5:
            style.update({
                'bg': '#FFEBEE',
                'fg': '#D32F2F'
            })
        # Обычные дни
        else:
            style.update({
                'bg': 'white',
                'fg': 'black'
            })

        return style

    def select_date(self, selected_date: date):
        """Выбор даты"""
        self.selected_date = selected_date
        self.update_calendar()

        if self.on_date_select:
            self.on_date_select(selected_date)


class TaskCalendarWindow:
    """Окно календаря с управлением задачами"""

    def __init__(self, parent, db_manager, task_manager=None):
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Календарь задач")
        self.window.geometry("800x600")

        self.setup_ui()

    def setup_ui(self):
        """Создание интерфейса окна календаря"""
        # Основной контейнер
        main_container = ttk.PanedWindow(self.window, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Левая панель - календарь
        calendar_frame = ttk.LabelFrame(main_container, text="Календарь")
        main_container.add(calendar_frame, weight=2)

        self.calendar = CalendarWidget(
            calendar_frame,
            on_date_select=self.on_date_selected,
            get_tasks_for_date=self.get_tasks_for_date
        )

        # Правая панель - задачи выбранного дня
        tasks_frame = ttk.LabelFrame(main_container, text="Задачи")
        main_container.add(tasks_frame, weight=1)

        # Заголовок с выбранной датой
        self.selected_date_label = ttk.Label(
            tasks_frame,
            text="Выберите дату",
            font=('Arial', 12, 'bold')
        )
        self.selected_date_label.pack(pady=5)

        # Список задач
        self.tasks_tree = ttk.Treeview(
            tasks_frame,
            columns=('title', 'priority', 'status'),
            show='headings',
            height=15
        )

        self.tasks_tree.heading('title', text='Название')
        self.tasks_tree.heading('priority', text='Приоритет')
        self.tasks_tree.heading('status', text='Статус')

        self.tasks_tree.column('title', width=200)
        self.tasks_tree.column('priority', width=80)
        self.tasks_tree.column('status', width=80)

        # Скроллбар для списка задач
        tasks_scrollbar = ttk.Scrollbar(tasks_frame, orient='vertical',
                                        command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=tasks_scrollbar.set)

        self.tasks_tree.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        tasks_scrollbar.pack(side='right', fill='y', pady=5)

        # Кнопки управления
        button_frame = ttk.Frame(tasks_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Перейти к дню",
                   command=self.go_to_selected_day).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Новая задача",
                   command=self.create_task_for_date).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Обновить",
                   command=self.refresh_tasks).pack(side='left')

        # Привязка двойного клика
        self.tasks_tree.bind('<Double-1>', self.on_task_double_click)

        # Инициализация с текущей датой
        self.on_date_selected(date.today())

    def get_tasks_for_date(self, target_date: date) -> List:
        """Получение задач для указанной даты"""
        try:
            date_str = target_date.isoformat()
            tasks = self.db.get_tasks(date_str)
            return [t for t in tasks if t.date_scheduled == date_str]
        except:
            return []

    def on_date_selected(self, selected_date: date):
        """Обработка выбора даты"""
        self.selected_date = selected_date

        # Обновление заголовка
        date_str = selected_date.strftime("%d %B %Y")
        weekday_names = [
            'Понедельник', 'Вторник', 'Среда', 'Четверг',
            'Пятница', 'Суббота', 'Воскресенье'
        ]
        weekday = weekday_names[selected_date.weekday()]
        self.selected_date_label.config(text=f"{weekday}, {date_str}")

        # Обновление списка задач
        self.refresh_tasks()

    def refresh_tasks(self):
        """Обновление списка задач"""
        # Очистка текущего списка
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Получение задач для выбранной даты
        tasks = self.get_tasks_for_date(self.selected_date)

        # Заполнение списка
        for task in tasks:
            status = "Выполнено" if task.is_completed else "В работе"
            priority_color = self.get_priority_display(task.priority)

            item = self.tasks_tree.insert('', 'end', values=(
                task.title,
                f"{task.priority}/10",
                status
            ))

            # Цветовое выделение выполненных задач
            if task.is_completed:
                self.tasks_tree.set(item, 'title', f"✓ {task.title}")

    def get_priority_display(self, priority: int) -> str:
        """Получение отображения приоритета"""
        return f"{priority}/10"

    def go_to_selected_day(self):
        """Переход к выбранному дню в основном интерфейсе"""
        if self.task_manager:
            self.task_manager.current_date = self.selected_date
            self.task_manager.refresh_task_list()
            self.window.destroy()

    def create_task_for_date(self):
        """Создание новой задачи для выбранной даты"""
        if self.task_manager:
            # Создание новой задачи с установленной датой
            new_task = self.task_manager.create_new_task_for_date(self.selected_date)
            self.refresh_tasks()
            self.calendar.update_calendar()

    def on_task_double_click(self, event):
        """Обработка двойного клика по задаче"""
        selection = self.tasks_tree.selection()
        if not selection:
            return

        item = selection[0]
        task_title = self.tasks_tree.item(item)['values'][0]

        # Поиск задачи по названию
        tasks = self.get_tasks_for_date(self.selected_date)
        for task in tasks:
            if task.title in task_title:
                if self.task_manager:
                    self.task_manager.select_task(task)
                    self.window.destroy()
                break


# Интеграция с основным классом TaskManager
class CalendarMixin:
    """Миксин для добавления функциональности календаря"""

    def show_calendar(self):
        """Показать окно календаря"""
        TaskCalendarWindow(self.root, self.db, self)

    def create_new_task_for_date(self, target_date: date):
        """Создание новой задачи для указанной даты"""
        from main import Task  # Импорт класса Task

        new_task = Task()
        new_task.date_scheduled = target_date.isoformat()
        new_task.title = f"Новая задача на {target_date.strftime('%d.%m.%Y')}"

        # Сохранение задачи
        new_task.id = self.db.save_task(new_task)

        return new_task


# Пример использования:
"""
Для интеграции с основным классом TaskManager:

class TaskManager(CalendarMixin):
    # ... существующий код ...
    pass

# Теперь метод show_calendar() будет работать корректно
"""