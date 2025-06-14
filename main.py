#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - Основной файл приложения с паттерном Observer
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Импорт модулей
from modules import (
    Task, TaskType, DatabaseManager,
    QuadrantsWidget, TaskListWidget, TaskDetailPanel,
    TaskEditDialog, CalendarWindow,
    get_priority_color, get_completed_color, UI_COLORS
)
from modules.event_manager import EventManager, EventType, Event


class TaskService:
    """Сервис для работы с задачами"""
    
    def __init__(self, db: DatabaseManager, event_manager: EventManager):
        self.db = db
        self.events = event_manager
        
    def create_task(self, task: Task) -> Task:
        """Создание новой задачи"""
        task.id = self.db.save_task(task)
        self.events.emit_now(EventType.TASK_CREATED, task)
        return task
    
    def update_task(self, task: Task) -> Task:
        """Обновление задачи"""
        self.db.save_task(task)
        self.events.emit_now(EventType.TASK_UPDATED, task)
        return task
    
    def delete_task(self, task_id: int):
        """Удаление задачи"""
        self.db.delete_task(task_id)
        self.events.emit_now(EventType.TASK_DELETED, task_id)
    
    def move_task_to_quadrant(self, task: Task, quadrant: int) -> Task:
        """Перемещение задачи в квадрант"""
        old_quadrant = task.quadrant
        task.quadrant = quadrant
        
        # Бизнес-логика перемещения
        if old_quadrant != quadrant and quadrant > 0:
            task.move_count += 1
            task.importance = min(10, task.importance + 1)
            task.priority = min(10, max(1, task.importance))
        
        self.db.save_task(task)
        self.events.emit_now(EventType.TASK_MOVED, {
            'task': task,
            'from_quadrant': old_quadrant,
            'to_quadrant': quadrant
        })
        return task
    
    def toggle_task_completion(self, task: Task, completed: bool) -> Task:
        """Переключение статуса выполнения"""
        task.is_completed = completed
        self.db.save_task(task)
        self.events.emit_now(EventType.TASK_COMPLETED, task)
        return task
    
    def get_tasks_for_date(self, date_str: str) -> Dict[int, List[Task]]:
        """Получение задач для даты, сгруппированных по квадрантам"""
        tasks = self.db.get_tasks(date_str, include_backlog=False)
        
        # Группировка по квадрантам
        quadrant_tasks = {i: [] for i in range(5)}
        for task in tasks:
            quadrant_tasks[task.quadrant].append(task)
        
        return quadrant_tasks


class TaskManager:
    """Основной класс приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg=UI_COLORS['background'])

        # Инициализация компонентов
        self.db = DatabaseManager()
        self.events = EventManager()
        self.task_service = TaskService(self.db, self.events)
        
        # Состояние приложения
        self.current_task: Optional[Task] = None
        self.current_date = datetime.now().date()
        self.day_started = False
        self.day_start_time = None
        
        # Кеш
        self.task_types_cache: List[TaskType] = []
        self._updating = False  # Флаг для предотвращения циклических обновлений

        # Подписка на события
        self.setup_event_handlers()

        # Создание интерфейса
        self.setup_ui()

        # Загрузка данных
        self.load_data()

    def setup_event_handlers(self):
        """Настройка обработчиков событий"""
        # События задач
        self.events.subscribe(EventType.TASK_CREATED, self.on_task_created)
        self.events.subscribe(EventType.TASK_UPDATED, self.on_task_updated)
        self.events.subscribe(EventType.TASK_DELETED, self.on_task_deleted)
        self.events.subscribe(EventType.TASK_MOVED, self.on_task_moved)
        self.events.subscribe(EventType.TASK_COMPLETED, self.on_task_completed)
        
        # События дня
        self.events.subscribe(EventType.DATE_CHANGED, self.on_date_changed)

    def on_task_created(self, event: Event):
        """Обработка создания задачи"""
        task = event.data
        logger.info(f"Task created: {task.title}")
        
        # Обновляем только если задача для текущей даты
        if task.date_scheduled == self.current_date.isoformat() or not task.date_scheduled:
            self.refresh_ui_for_task(task)

    def on_task_updated(self, event: Event):
        """Обработка обновления задачи"""
        task = event.data
        logger.info(f"Task updated: {task.title}")
        
        # Обновляем текущую задачу если это она
        if self.current_task and self.current_task.id == task.id:
            self.current_task = task
            self.task_detail_panel.show_task(task)
        
        self.refresh_ui_for_task(task)

    def on_task_deleted(self, event: Event):
        """Обработка удаления задачи"""
        task_id = event.data
        logger.info(f"Task deleted: {task_id}")
        
        # Очищаем выбор если удалена текущая задача
        if self.current_task and self.current_task.id == task_id:
            self.current_task = None
            self.task_detail_panel.show_no_task()
        
        self.refresh_ui()

    def on_task_moved(self, event: Event):
        """Обработка перемещения задачи"""
        data = event.data
        task = data['task']
        from_quad = data['from_quadrant']
        to_quad = data['to_quadrant']
        
        logger.info(f"Task moved: {task.title} from {from_quad} to {to_quad}")
        
        # Обновляем UI
        self.refresh_ui_for_task(task)
        
        # Обновляем текущую задачу если это она
        if self.current_task and self.current_task.id == task.id:
            self.current_task = task
            self.task_detail_panel.show_task(task)

    def on_task_completed(self, event: Event):
        """Обработка выполнения задачи"""
        task = event.data
        logger.info(f"Task completed status changed: {task.title} -> {task.is_completed}")
        self.refresh_ui_for_task(task)

    def on_date_changed(self, event: Event):
        """Обработка изменения даты"""
        self.refresh_ui()

    def refresh_ui(self):
        """Полное обновление UI"""
        if self._updating:
            return
            
        self._updating = True
        try:
            # Получаем все задачи для текущей даты
            quadrant_tasks = self.task_service.get_tasks_for_date(self.current_date.isoformat())
            all_tasks = []
            for tasks in quadrant_tasks.values():
                all_tasks.extend(tasks)
            
            # Обновляем виджеты
            self.quadrants_widget.update_quadrants(quadrant_tasks)
            self.task_list_widget.update_tasks(all_tasks)
            
        finally:
            self._updating = False

    def refresh_ui_for_task(self, task: Task):
        """Частичное обновление UI для конкретной задачи"""
        if self._updating:
            return
            
        # Для упрощения делаем полное обновление
        # В будущем можно оптимизировать для обновления только нужных частей
        self.refresh_ui()

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

        # Верхняя панель
        self.setup_top_panel(main_container)

        # Средняя панель
        self.setup_responsive_layout(main_container)

        # Нижняя панель деталей
        self.task_detail_panel = TaskDetailPanel(main_container, self)

        # Обновление времени
        self.update_datetime()

    def setup_top_panel(self, parent):
        """Настройка верхней панели"""
        top_panel = ttk.Frame(parent)
        top_panel.pack(fill='x', pady=(0, 10))

        # Дата и время
        self.datetime_label = ttk.Label(top_panel, font=('Arial', 12, 'bold'))
        self.datetime_label.pack(side='left')

        # Кнопки управления
        self.day_btn = ttk.Button(top_panel, text="Начать день",
                                  command=self.toggle_day_state)
        self.day_btn.pack(side='right', padx=(5, 0))

        self.calendar_btn = ttk.Button(top_panel, text="Календарь",
                                       command=self.show_calendar)
        self.calendar_btn.pack(side='right', padx=(5, 0))

        self.backlog_btn = ttk.Button(top_panel, text="Бэклог",
                                      command=self.show_backlog)
        self.backlog_btn.pack(side='right', padx=(5, 0))

    def setup_responsive_layout(self, parent):
        """Настройка responsive layout"""
        # Основной контейнер
        self.layout_container = ttk.Frame(parent)
        self.layout_container.pack(fill='both', expand=True)

        # Создание компонентов с передачей event manager
        self.quadrants_widget = QuadrantsWidget(self.layout_container, self)
        self.task_list_widget = TaskListWidget(self.layout_container, self)

        # Начальная компоновка
        self.switch_to_horizontal_layout()

        # Привязка события изменения размера
        self.root.bind('<Configure>', self.on_window_resize)

    def on_window_resize(self, event):
        """Обработка изменения размера окна"""
        if event.widget == self.root:
            width = self.root.winfo_width()

            # При ширине меньше 900px переносим задачи под планирование
            if width < 900:
                self.switch_to_vertical_layout()
            else:
                self.switch_to_horizontal_layout()

    def switch_to_vertical_layout(self):
        """Переключение на вертикальную компоновку"""
        self.quadrants_widget.main_frame.pack_forget()
        self.task_list_widget.main_frame.pack_forget()

        self.quadrants_widget.main_frame.pack(side='top', fill='both', expand=True)
        self.task_list_widget.main_frame.pack(side='bottom', fill='x', pady=(10, 0))

    def switch_to_horizontal_layout(self):
        """Переключение на горизонтальную компоновку"""
        self.quadrants_widget.main_frame.pack_forget()
        self.task_list_widget.main_frame.pack_forget()

        self.quadrants_widget.main_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.task_list_widget.main_frame.pack(side='right', fill='y', padx=(10, 0))

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
        self.root.bind('<Control-n>', lambda e: self.create_new_task_dialog())
        self.root.bind('<Control-s>', lambda e: self.quick_save_task())
        self.root.bind('<Control-d>', lambda e: self.delete_current_task())
        self.root.bind('<F1>', lambda e: self.show_hotkeys())

    def show_hotkeys(self):
        """Показать окно горячих клавиш"""
        hotkey_window = tk.Toplevel(self.root)
        hotkey_window.title("Горячие клавиши")
        hotkey_window.geometry("400x300")

        hotkeys = [
            ("Ctrl+N", "Новая задача"),
            ("Ctrl+S", "Быстрое сохранение"),
            ("Ctrl+D", "Удалить задачу"),
            ("F1", "Показать горячие клавиши"),
        ]

        for key, description in hotkeys:
            frame = ttk.Frame(hotkey_window)
            frame.pack(fill='x', padx=10, pady=2)
            ttk.Label(frame, text=key, font=('Arial', 10, 'bold')).pack(side='left')
            ttk.Label(frame, text=description).pack(side='left', padx=(20, 0))

    # Методы работы с задачами
    def create_new_task_dialog(self):
        """Создание новой задачи через диалог"""
        dialog = TaskEditDialog(self.root, self)
        if dialog.result:
            messagebox.showinfo("Успех", "Задача создана!")

    def edit_current_task(self):
        """Редактирование текущей задачи"""
        if not self.current_task:
            messagebox.showwarning("Предупреждение", "Выберите задачу для редактирования!")
            return

        dialog = TaskEditDialog(self.root, self, self.current_task)
        if dialog.result:
            self.current_task = dialog.result
            messagebox.showinfo("Успех", "Задача обновлена!")

    def quick_save_task(self):
        """Быстрое сохранение текущей задачи"""
        if self.current_task:
            self.task_service.update_task(self.current_task)
            messagebox.showinfo("Успех", "Задача сохранена!")

    def delete_current_task(self):
        """Удаление текущей задачи"""
        if not self.current_task or self.current_task.id == 0:
            messagebox.showwarning("Предупреждение", "Нет задачи для удаления!")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{self.current_task.title}'?"):
            self.task_service.delete_task(self.current_task.id)
            messagebox.showinfo("Успех", "Задача удалена!")

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.current_task = task
        self.task_detail_panel.show_task(task)

    def toggle_task_completion(self, task: Task, completed: bool):
        """Переключение статуса выполнения"""
        self.task_service.toggle_task_completion(task, completed)

    def move_task_to_quadrant(self, task: Task, quadrant: int):
        """Перемещение задачи в квадрант"""
        logger.info(f"Moving task '{task.title}' to quadrant {quadrant}")
        
        # Устанавливаем дату если её нет
        if not task.date_scheduled and quadrant > 0:
            task.date_scheduled = self.current_date.isoformat()
        
        self.task_service.move_task_to_quadrant(task, quadrant)

    def move_task_to_backlog(self, task: Task):
        """Перемещение задачи в бэклог"""
        logger.info(f"Moving task to backlog: {task.title}")
        
        task.date_scheduled = ""
        task.quadrant = 0
        
        self.task_service.update_task(task)

    # Управление днем
    def start_day(self):
        """Начало планирования дня"""
        if not self.day_started:
            self.day_started = True
            self.day_start_time = datetime.now()

            start_hour = self.day_start_time.hour
            start_minute = self.day_start_time.minute
            self.quadrants_widget.update_time_labels(start_hour, start_minute)

            self.day_btn.config(text="Завершить день")
            self.events.emit_now(EventType.DAY_STARTED, self.day_start_time)
            messagebox.showinfo("День начат", f"День начат в {self.day_start_time.strftime('%H:%M')}")

    def end_day(self):
        """Завершение дня"""
        if self.day_started:
            if messagebox.askyesno("Завершение дня", "Завершить текущий день?"):
                self.day_started = False

                end_time = datetime.now()
                self.db.save_setting(f"day_end_{self.current_date.isoformat()}", end_time.isoformat())

                self.current_date += timedelta(days=1)
                self.day_btn.config(text="Начать день")
                
                self.events.emit_now(EventType.DAY_ENDED, end_time)
                self.events.emit_now(EventType.DATE_CHANGED, self.current_date)

                messagebox.showinfo("День завершен", f"День завершен в {end_time.strftime('%H:%M')}")

    def toggle_day_state(self):
        """Переключение состояния дня"""
        if self.day_started:
            self.end_day()
        else:
            self.start_day()

    def show_calendar(self):
        """Показать календарь"""
        CalendarWindow(self.root, self.db, self)

    def show_backlog(self):
        """Показать бэклог"""
        from modules.backlog_window import BacklogWindow
        BacklogWindow(self.root, self.db, self)

    def go_to_date(self, target_date: date):
        """Переход к указанной дате"""
        self.current_date = target_date
        self.update_datetime()
        self.task_detail_panel.show_no_task()
        
        self.events.emit_now(EventType.DATE_CHANGED, target_date)

        if target_date == date.today():
            msg = "Переход к сегодняшнему дню"
        elif target_date < date.today():
            msg = f"Переход к прошедшему дню: {target_date.strftime('%d.%m.%Y')}"
        else:
            msg = f"Переход к будущему дню: {target_date.strftime('%d.%m.%Y')}"

        messagebox.showinfo("Переход к дню", msg)

    def update_analytics(self):
        """Обновление аналитики"""
        for item in self.analytics_tree.get_children():
            self.analytics_tree.delete(item)

        all_tasks = self.db.get_tasks()

        days_data = {}
        for task in all_tasks:
            if task.date_scheduled:
                date = task.date_scheduled
                if date not in days_data:
                    days_data[date] = {'completed': 0, 'total_difficulty': 0}

                if task.is_completed:
                    days_data[date]['completed'] += 1
                    days_data[date]['total_difficulty'] += task.importance

        for date, data in sorted(days_data.items(), reverse=True):
            self.analytics_tree.insert('', 'end', values=(
                date,
                data['completed'],
                data['total_difficulty']
            ))

    def update_datetime(self):
        """Обновление отображения даты и времени"""
        now = datetime.now()

        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

        weekday = weekdays[self.current_date.weekday()]
        month = months[self.current_date.month - 1]

        date_str = f"{weekday}, {self.current_date.day} {month} {self.current_date.year}"
        time_str = now.strftime("%H:%M:%S")

        if self.current_date == date.today():
            self.datetime_label.config(text=f"{date_str} | {time_str}")
        else:
            self.datetime_label.config(text=f"{date_str} (просмотр)")

        self.root.after(1000, self.update_datetime)

    def get_task_types(self, force_refresh: bool = False) -> List[TaskType]:
        """Получение типов задач с кешированием"""
        if force_refresh or not self.task_types_cache:
            self.task_types_cache = self.db.get_task_types()
        return self.task_types_cache

    def load_data(self):
        """Загрузка данных при запуске"""
        self.refresh_ui()
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