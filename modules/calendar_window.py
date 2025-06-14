# -*- coding: utf-8 -*-
"""
Task Manager - Окно календаря
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date
from typing import List
from .task_models import Task
from .task_edit_dialog import TaskEditDialog


class CalendarWindow:
    """Окно календаря"""

    def __init__(self, parent, db_manager, task_manager=None):
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Календарь задач")
        self.window.geometry("900x600")

        self.current_date = date.today()
        self.selected_date = date.today()

        self.setup_ui()

    def setup_ui(self):
        """Создание интерфейса"""
        main_container = ttk.PanedWindow(self.window, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Левая панель - календарь
        calendar_frame = ttk.LabelFrame(main_container, text="Календарь")
        main_container.add(calendar_frame, weight=2)

        self.setup_calendar(calendar_frame)

        # Правая панель - задачи
        tasks_frame = ttk.LabelFrame(main_container, text="Задачи")
        main_container.add(tasks_frame, weight=1)

        self.setup_tasks_panel(tasks_frame)

        # Инициализация
        self.update_calendar()
        self.on_date_selected(date.today())

    def setup_calendar(self, parent):
        """Создание календаря"""
        # Заголовок с навигацией
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))

        # Кнопки навигации
        ttk.Button(header_frame, text="<<", command=self.prev_year, width=3).pack(side='left')
        ttk.Button(header_frame, text="<", command=self.prev_month, width=3).pack(side='left', padx=(5, 0))

        # Месяц и год
        self.month_year_label = ttk.Label(header_frame, font=('Arial', 14, 'bold'))
        self.month_year_label.pack(side='left', expand=True)

        ttk.Button(header_frame, text=">", command=self.next_month, width=3).pack(side='right', padx=(0, 5))
        ttk.Button(header_frame, text=">>", command=self.next_year, width=3).pack(side='right')

        # Кнопка "Сегодня"
        ttk.Button(header_frame, text="Сегодня", command=self.go_to_today).pack(side='right', padx=(0, 10))

        # Сетка календаря
        self.calendar_frame = ttk.Frame(parent)
        self.calendar_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Заголовки дней недели
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            label = ttk.Label(self.calendar_frame, text=day, font=('Arial', 10, 'bold'), anchor='center')
            label.grid(row=0, column=i, sticky='ew', padx=1, pady=1)

        # Настройка колонок
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)

        self.day_buttons = {}

    def setup_tasks_panel(self, parent):
        """Создание панели задач"""
        # Заголовок с датой
        self.selected_date_label = ttk.Label(parent, text="Выберите дату",
                                           font=('Arial', 12, 'bold'))
        self.selected_date_label.pack(pady=5)

        # Список задач
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.tasks_tree = ttk.Treeview(list_frame,
                                      columns=('title', 'urgency', 'status'),
                                      show='headings', height=15)

        self.tasks_tree.heading('title', text='Название')
        self.tasks_tree.heading('urgency', text='Срочность')
        self.tasks_tree.heading('status', text='Статус')

        self.tasks_tree.column('title', width=200)
        self.tasks_tree.column('urgency', width=80)
        self.tasks_tree.column('status', width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)

        self.tasks_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Кнопки
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Перейти к дню", command=self.go_to_selected_day).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Новая задача", command=self.create_task_for_date).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Обновить", command=self.refresh_tasks).pack(side='left')

        # События
        self.tasks_tree.bind('<Double-1>', self.on_task_double_click)

    def prev_month(self):
        """Предыдущий месяц"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()

    def next_month(self):
        """Следующий месяц"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()

    def prev_year(self):
        """Предыдущий год"""
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self.update_calendar()

    def next_year(self):
        """Следующий год"""
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self.update_calendar()

    def go_to_today(self):
        """Перейти к сегодня"""
        self.current_date = date.today()
        self.selected_date = date.today()
        self.update_calendar()
        self.on_date_selected(self.selected_date)

    def update_calendar(self):
        """Обновление календаря"""
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

        # Создание кнопок дней
        for week_num, week in enumerate(cal, start=1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue

                day_date = date(self.current_date.year, self.current_date.month, day)

                # Стиль дня
                style = self.get_day_style(day_date)

                day_btn = tk.Button(
                    self.calendar_frame,
                    text=str(day),
                    command=lambda d=day_date: self.select_date(d),
                    width=8, height=3,
                    font=('Arial', 10),
                    **style
                )
                day_btn.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)

                # Добавляем информацию о задачах
                tasks = self.get_tasks_for_date(day_date)
                if tasks:
                    task_count = len(tasks)
                    completed_count = sum(1 for t in tasks if t.is_completed)
                    info_text = f"{day}\n({completed_count}/{task_count})"
                    day_btn.config(text=info_text, font=('Arial', 8))

                self.day_buttons[day_date] = day_btn

        # Настройка строк
        for i in range(len(cal) + 1):
            self.calendar_frame.grid_rowconfigure(i, weight=1)

    def get_day_style(self, day_date: date) -> dict:
        """Получение стиля для дня"""
        today = date.today()

        style = {
            'relief': 'raised',
            'bd': 1
        }

        if day_date == today:
            style.update({'bg': '#2196F3', 'fg': 'white', 'font': ('Arial', 10, 'bold')})
        elif day_date == self.selected_date:
            style.update({'bg': '#FFC107', 'fg': 'black', 'font': ('Arial', 10, 'bold')})
        elif day_date.weekday() >= 5:  # Выходные
            style.update({'bg': '#FFEBEE', 'fg': '#D32F2F'})
        else:
            style.update({'bg': 'white', 'fg': 'black'})

        return style

    def select_date(self, selected_date: date):
        """Выбор даты"""
        old_selected = self.selected_date
        self.selected_date = selected_date

        # Обновляем стили кнопок
        if old_selected in self.day_buttons:
            old_style = self.get_day_style(old_selected)
            self.day_buttons[old_selected].config(**old_style)

        if selected_date in self.day_buttons:
            new_style = self.get_day_style(selected_date)
            self.day_buttons[selected_date].config(**new_style)

        self.on_date_selected(selected_date)

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        """Получение задач для даты"""
        try:
            date_str = target_date.isoformat()
            tasks = self.db.get_tasks(date_str, include_backlog=False)
            return tasks
        except:
            return []

    def on_date_selected(self, selected_date: date):
        """Обработка выбора даты"""
        # Обновление заголовка
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

        weekday = weekdays[selected_date.weekday()]
        month = months[selected_date.month - 1]
        formatted_date = f"{selected_date.day} {month} {selected_date.year}"

        self.selected_date_label.config(text=f"{weekday}, {formatted_date}")
        self.refresh_tasks()

    def refresh_tasks(self):
        """Обновление списка задач"""
        # Очистка
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Загрузка задач
        tasks = self.get_tasks_for_date(self.selected_date)

        for task in tasks:
            status = "Выполнено" if task.is_completed else "В работе"
            title = task.title
            if task.is_planned:
                title = f"📅 {title}"

            item = self.tasks_tree.insert('', 'end', values=(
                title,
                f"{task.priority}/10",
                status
            ))

            if task.is_completed:
                self.tasks_tree.set(item, 'title', f"✓ {title}")

    def go_to_selected_day(self):
        """Переход к выбранному дню"""
        if self.task_manager:
            self.task_manager.go_to_date(self.selected_date)
            self.window.destroy()

    def create_task_for_date(self):
        """Создание задачи для выбранной даты"""
        if self.task_manager:
            # Создаем новую задачу
            new_task = Task()
            new_task.date_scheduled = self.selected_date.isoformat()

            dialog = TaskEditDialog(self.window, self.task_manager, new_task)
            if dialog.result:
                self.refresh_tasks()
                self.update_calendar()

    def on_task_double_click(self, event):
        """Двойной клик по задаче"""
        selection = self.tasks_tree.selection()
        if not selection:
            return

        item = selection[0]
        task_values = self.tasks_tree.item(item)['values']
        if not task_values:
            return

        task_title = task_values[0]
        clean_title = task_title.replace("📅 ", "").replace("✓ ", "")

        # Находим задачу
        tasks = self.get_tasks_for_date(self.selected_date)
        for task in tasks:
            if task.title == clean_title:
                if self.task_manager:
                    self.task_manager.go_to_date(self.selected_date)
                    self.task_manager.select_task(task)
                    self.window.destroy()
                break