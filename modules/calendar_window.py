# -*- coding: utf-8 -*-
"""
Task Manager - Оптимизированное окно календаря с инкрементальными обновлениями
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date, timedelta
from typing import List, Dict, Set, Optional
import logging

from .task_models import Task
from .task_edit_dialog import TaskEditDialog
from .incremental_updater import SmartUpdateMixin

logger = logging.getLogger(__name__)


class CalendarWindow(SmartUpdateMixin):
    """Оптимизированное окно календаря с инкрементальными обновлениями"""

    def __init__(self, parent, db_manager, task_manager=None):
        super().__init__()
        self.parent = parent
        self.db = db_manager
        self.task_manager = task_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Календарь задач")
        self.window.geometry("900x600")

        self.current_date = date.today()
        self.selected_date = date.today()
        
        # Кеши
        self.day_buttons = {}  # date -> button widget
        self.day_tasks_cache = {}  # date -> list of tasks
        self.month_tasks_cache = {}  # (year, month) -> {date: tasks}
        self.button_states = {}  # date -> (text, bg_color, fg_color)
        
        self.setup_ui()
        self.initial_load()

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
        ttk.Button(button_frame, text="Обновить", command=self.refresh_current_month).pack(side='left')

        # События
        self.tasks_tree.bind('<Double-1>', self.on_task_double_click)

    def initial_load(self):
        """Начальная загрузка"""
        self.update_month_header()
        self.load_month_tasks(self.current_date.year, self.current_date.month)
        self.create_month_buttons()
        self.on_date_selected(date.today())

    def prev_month(self):
        """Предыдущий месяц"""
        if self.current_date.month == 1:
            new_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            new_date = self.current_date.replace(month=self.current_date.month - 1)
        
        self.change_month(new_date)

    def next_month(self):
        """Следующий месяц"""
        if self.current_date.month == 12:
            new_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            new_date = self.current_date.replace(month=self.current_date.month + 1)
        
        self.change_month(new_date)

    def prev_year(self):
        """Предыдущий год"""
        new_date = self.current_date.replace(year=self.current_date.year - 1)
        self.change_month(new_date)

    def next_year(self):
        """Следующий год"""
        new_date = self.current_date.replace(year=self.current_date.year + 1)
        self.change_month(new_date)

    def go_to_today(self):
        """Перейти к сегодня"""
        today = date.today()
        if self.current_date.year != today.year or self.current_date.month != today.month:
            self.change_month(today)
        self.select_date(today)

    def change_month(self, new_date: date):
        """Смена месяца с оптимизацией"""
        old_year, old_month = self.current_date.year, self.current_date.month
        new_year, new_month = new_date.year, new_date.month
        
        self.current_date = new_date
        self.update_month_header()
        
        # Загружаем задачи для нового месяца если их нет в кеше
        if (new_year, new_month) not in self.month_tasks_cache:
            self.load_month_tasks(new_year, new_month)
        
        # Инкрементальное обновление кнопок
        self.update_month_buttons_incremental()

    def update_month_header(self):
        """Обновление заголовка месяца"""
        month_names = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_name = month_names[self.current_date.month - 1]
        self.month_year_label.config(text=f"{month_name} {self.current_date.year}")

    def load_month_tasks(self, year: int, month: int):
        """Загрузка всех задач месяца одним запросом"""
        logger.debug(f"Loading tasks for {year}-{month}")
        
        # Определяем диапазон дат месяца
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Получаем все задачи
        all_tasks = self.db.get_tasks()
        
        # Фильтруем и группируем по датам
        month_tasks = {}
        for task in all_tasks:
            if task.date_scheduled:
                try:
                    task_date = datetime.strptime(task.date_scheduled, '%Y-%m-%d').date()
                    if first_day <= task_date <= last_day:
                        if task_date not in month_tasks:
                            month_tasks[task_date] = []
                        month_tasks[task_date].append(task)
                except:
                    pass
        
        # Сохраняем в кеш
        self.month_tasks_cache[(year, month)] = month_tasks
        
        # Обновляем кеш отдельных дней
        for day_date, tasks in month_tasks.items():
            self.day_tasks_cache[day_date] = tasks

    def create_month_buttons(self):
        """Создание всех кнопок месяца"""
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Создаем кнопки для всех дней
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                
                day_date = date(self.current_date.year, self.current_date.month, day)
                
                # Создаем кнопку если её еще нет
                if day_date not in self.day_buttons:
                    btn = tk.Button(
                        self.calendar_frame,
                        width=8, height=3,
                        command=lambda d=day_date: self.select_date(d)
                    )
                    btn.grid(row=week_num + 1, column=day_num, sticky='nsew', padx=1, pady=1)
                    self.day_buttons[day_date] = btn
                
                # Обновляем кнопку
                self.update_day_button(day_date)
        
        # Настройка строк
        for i in range(len(cal) + 1):
            self.calendar_frame.grid_rowconfigure(i, weight=1)

    def update_month_buttons_incremental(self):
        """Инкрементальное обновление кнопок при смене месяца"""
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Собираем все даты текущего месяца
        current_month_dates = set()
        for week in cal:
            for day in week:
                if day > 0:
                    current_month_dates.add(date(self.current_date.year, self.current_date.month, day))
        
        # Скрываем кнопки других месяцев
        for day_date, btn in self.day_buttons.items():
            if day_date not in current_month_dates:
                btn.grid_remove()
        
        # Обновляем/показываем кнопки текущего месяца
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Пустая ячейка - создаем невидимый Frame для правильной сетки
                    placeholder = tk.Frame(self.calendar_frame)
                    placeholder.grid(row=week_num + 1, column=day_num)
                    continue
                
                day_date = date(self.current_date.year, self.current_date.month, day)
                
                if day_date in self.day_buttons:
                    # Показываем существующую кнопку
                    btn = self.day_buttons[day_date]
                    btn.grid(row=week_num + 1, column=day_num, sticky='nsew', padx=1, pady=1)
                else:
                    # Создаем новую кнопку
                    btn = tk.Button(
                        self.calendar_frame,
                        width=8, height=3,
                        command=lambda d=day_date: self.select_date(d)
                    )
                    btn.grid(row=week_num + 1, column=day_num, sticky='nsew', padx=1, pady=1)
                    self.day_buttons[day_date] = btn
                
                # Обновляем только если изменилось состояние
                self.update_day_button_if_changed(day_date)

    def update_day_button(self, day_date: date):
        """Обновление одной кнопки дня"""
        if day_date not in self.day_buttons:
            return
        
        btn = self.day_buttons[day_date]
        
        # Получаем стиль
        style = self.get_day_style(day_date)
        
        # Получаем задачи из кеша
        tasks = self.get_cached_tasks_for_date(day_date)
        
        # Формируем текст
        if tasks:
            task_count = len(tasks)
            completed_count = sum(1 for t in tasks if t.is_completed)
            text = f"{day_date.day}\n({completed_count}/{task_count})"
            font = ('Arial', 8)
        else:
            text = str(day_date.day)
            font = style.get('font', ('Arial', 10))
        
        # Применяем стиль
        btn.config(text=text, **style)
        
        # Сохраняем состояние
        self.button_states[day_date] = (text, style.get('bg'), style.get('fg'))

    def update_day_button_if_changed(self, day_date: date):
        """Обновление кнопки только если изменилось состояние"""
        if day_date not in self.day_buttons:
            return
        
        # Получаем новое состояние
        style = self.get_day_style(day_date)
        tasks = self.get_cached_tasks_for_date(day_date)
        
        if tasks:
            task_count = len(tasks)
            completed_count = sum(1 for t in tasks if t.is_completed)
            new_text = f"{day_date.day}\n({completed_count}/{task_count})"
        else:
            new_text = str(day_date.day)
        
        new_bg = style.get('bg')
        new_fg = style.get('fg')
        
        # Проверяем изменения
        old_state = self.button_states.get(day_date, (None, None, None))
        if (new_text, new_bg, new_fg) != old_state:
            self.update_day_button(day_date)

    def get_cached_tasks_for_date(self, target_date: date) -> List[Task]:
        """Получение задач из кеша"""
        # Сначала проверяем кеш дня
        if target_date in self.day_tasks_cache:
            return self.day_tasks_cache[target_date]
        
        # Затем кеш месяца
        month_key = (target_date.year, target_date.month)
        if month_key in self.month_tasks_cache:
            tasks = self.month_tasks_cache[month_key].get(target_date, [])
            self.day_tasks_cache[target_date] = tasks
            return tasks
        
        # Если нет в кеше - пустой список (не делаем запрос к БД)
        return []

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
        """Выбор даты с оптимизацией"""
        if selected_date == self.selected_date:
            return  # Не обновляем если дата не изменилась
        
        old_selected = self.selected_date
        self.selected_date = selected_date
        
        # Обновляем только две кнопки - старую и новую
        if old_selected in self.day_buttons:
            self.update_day_button_if_changed(old_selected)
        
        if selected_date in self.day_buttons:
            self.update_day_button_if_changed(selected_date)
        
        self.on_date_selected(selected_date)

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
        self.refresh_tasks_list()

    def refresh_tasks_list(self):
        """Обновление списка задач для выбранной даты"""
        # Очистка
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Получаем задачи из кеша
        tasks = self.get_cached_tasks_for_date(self.selected_date)

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

    def refresh_current_month(self):
        """Обновление текущего месяца"""
        # Очищаем кеш месяца
        month_key = (self.current_date.year, self.current_date.month)
        if month_key in self.month_tasks_cache:
            del self.month_tasks_cache[month_key]
        
        # Перезагружаем задачи
        self.load_month_tasks(self.current_date.year, self.current_date.month)
        
        # Обновляем только видимые кнопки
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        for week in cal:
            for day in week:
                if day > 0:
                    day_date = date(self.current_date.year, self.current_date.month, day)
                    self.update_day_button_if_changed(day_date)
        
        # Обновляем список задач для текущей даты
        self.refresh_tasks_list()

    def go_to_selected_day(self):
        """Переход к выбранному дню"""
        if self.task_manager:
            self.task_manager.go_to_date(self.selected_date)
            self.window.destroy()

    def create_task_for_date(self):
        """Создание задачи для выбранной даты"""
        if self.task_manager:
            # Создаем новую задачу для выбранной даты
            new_task = Task()
            new_task.date_scheduled = self.selected_date.isoformat()

            dialog = TaskEditDialog(self.window, self.task_manager, new_task)
            if dialog.result:
                # Обновляем только нужный день
                self.queue_update(self._refresh_single_day, self.selected_date)

    def _refresh_single_day(self, day_date: date):
        """Обновление одного дня после изменения"""
        # Удаляем из кеша
        if day_date in self.day_tasks_cache:
            del self.day_tasks_cache[day_date]
        
        # Получаем новые задачи
        try:
            date_str = day_date.isoformat()
            tasks = self.db.get_tasks(date_str, include_backlog=False)
            self.day_tasks_cache[day_date] = tasks
            
            # Обновляем кнопку
            self.update_day_button_if_changed(day_date)
            
            # Если это выбранная дата - обновляем список
            if day_date == self.selected_date:
                self.refresh_tasks_list()
        except Exception as e:
            logger.error(f"Error refreshing day {day_date}: {e}")

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
        tasks = self.get_cached_tasks_for_date(self.selected_date)
        for task in tasks:
            if task.title == clean_title:
                if self.task_manager:
                    self.task_manager.go_to_date(self.selected_date)
                    self.task_manager.select_task(task)
                    self.window.destroy()
                break