#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - Основной файл приложения (исправленная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from typing import Optional

# Импорт модулей
from modules import (
    Task, TaskType, DatabaseManager,
    get_priority_color, UI_COLORS,
    FullScreenQuadrantsWidget, CompactTaskListWidget, TaskEditDialog,
    CalendarMixin, DragDropMixin
)


class TaskManager(DragDropMixin, CalendarMixin):
    """Основной класс приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg=UI_COLORS['background'])

        # Инициализация компонентов
        self.db = DatabaseManager()
        self.current_task: Optional[Task] = None
        self.current_date = datetime.now().date()
        self.day_started = False
        self.day_start_time = None

        # Создание интерфейса
        self.setup_ui()

        # Инициализация дополнительных модулей
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
        """Настройка основной вкладки с responsive дизайном"""
        # Основной контейнер
        main_container = ttk.Frame(self.task_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Верхняя панель с информацией и кнопками
        self.setup_top_panel(main_container)

        # Средняя панель с грид-структурой
        self.setup_responsive_layout(main_container)

        # Обновление времени
        self.update_datetime()

    def setup_top_panel(self, parent):
        """Настройка верхней панели"""
        top_panel = ttk.Frame(parent)
        top_panel.pack(fill='x', pady=(0, 10))

        # Дата и время
        self.datetime_label = ttk.Label(top_panel, font=('Arial', 12, 'bold'))
        self.datetime_label.pack(side='left')

        # Кнопки управления днем
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
        """Настройка responsive layout с грид-структурой"""
        # Основной контейнер с возможностью перестройки
        self.layout_container = ttk.Frame(parent)
        self.layout_container.pack(fill='both', expand=True)

        # Создание компонентов
        self.quadrants_widget = FullScreenQuadrantsWidget(self.layout_container, self)
        self.task_list_widget = CompactTaskListWidget(self.layout_container, self)

        # Привязка события изменения размера
        self.root.bind('<Configure>', self.on_window_resize)

    def on_window_resize(self, event):
        """Обработка изменения размера окна для responsive дизайна"""
        if event.widget == self.root:
            width = self.root.winfo_width()

            # При ширине меньше 900px переносим задачи под планирование
            if width < 900:
                self.switch_to_vertical_layout()
            else:
                self.switch_to_horizontal_layout()

    def switch_to_vertical_layout(self):
        """Переключение на вертикальную компоновку"""
        # Перепаковываем виджеты
        self.quadrants_widget.main_frame.pack_forget()
        self.task_list_widget.main_frame.pack_forget()

        self.quadrants_widget.main_frame.pack(side='top', fill='both', expand=True)
        self.task_list_widget.main_frame.pack(side='bottom', fill='x', pady=(10, 0))

    def switch_to_horizontal_layout(self):
        """Переключение на горизонтальную компоновку"""
        # Перепаковываем виджеты
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

    # Основные методы работы с задачами
    def create_new_task_dialog(self):
        """Создание новой задачи через диалог"""
        dialog = TaskEditDialog(self.root, self)
        if dialog.result:
            self.refresh_task_list()
            messagebox.showinfo("Успех", "Задача создана!")

    def edit_current_task(self):
        """Редактирование текущей задачи через диалог"""
        if not self.current_task:
            messagebox.showwarning("Предупреждение", "Выберите задачу для редактирования!")
            return

        dialog = TaskEditDialog(self.root, self, self.current_task)
        if dialog.result:
            self.current_task = dialog.result
            self.refresh_task_list()
            messagebox.showinfo("Успех", "Задача обновлена!")

    def quick_save_task(self):
        """Быстрое сохранение текущей задачи"""
        if self.current_task:
            self.db.save_task(self.current_task)
            messagebox.showinfo("Успех", "Задача сохранена!")

    def delete_current_task(self):
        """Удаление текущей задачи"""
        if not self.current_task or self.current_task.id == 0:
            messagebox.showwarning("Предупреждение", "Нет задачи для удаления!")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{self.current_task.title}'?"):
            self.db.delete_task(self.current_task.id)
            self.current_task = None
            self.refresh_task_list()
            messagebox.showinfo("Успех", "Задача удалена!")

    def refresh_task_list(self):
        """Обновление списка задач"""
        # Очистка текущего списка
        self.task_list_widget.clear_tasks()

        # Получение задач только для текущей даты (не бэклог)
        date_str = self.current_date.isoformat()
        tasks = self.db.get_tasks(date_str, include_backlog=False)

        # Создание блоков для задач
        for task in tasks:
            self.task_list_widget.add_task_button(task)

        # Обновление квадрантов
        self.refresh_quadrants(tasks)

    def refresh_quadrants(self, tasks):
        """Обновление отображения квадрантов"""
        self.quadrants_widget.clear_quadrants()

        # Размещение задач в квадрантах
        for task in tasks:
            if 1 <= task.quadrant <= 4:
                self.quadrants_widget.add_task_to_quadrant(task, task.quadrant)

    def select_task(self, task: Task):
        """Выбор задачи для отображения информации"""
        self.current_task = task
        # Можно добавить отображение информации о задаче в статусной строке

    def toggle_task_completion(self, task: Task, completed: bool):
        """Переключение статуса выполнения задачи"""
        task.is_completed = completed
        self.db.save_task(task)

        if self.current_task and self.current_task.id == task.id:
            self.current_task.is_completed = completed

        self.refresh_task_list()

    # Методы управления днем
    def start_day(self):
        """Начало планирования дня"""
        if not self.day_started:
            self.day_started = True
            self.day_start_time = datetime.now().time()

            start_hour = self.day_start_time.hour

            # Исправляем проблему с временем 25:00
            self.quadrants_widget.update_time_labels(start_hour)

            self.day_btn.config(text="Завершить день")
            messagebox.showinfo("День начат", f"День начат в {self.day_start_time.strftime('%H:%M')}")

    def end_day(self):
        """Завершение дня"""
        if self.day_started:
            if messagebox.askyesno("Завершение дня", "Завершить текущий день?"):
                self.day_started = False

                end_time = datetime.now().time()
                self.db.save_setting(f"day_end_{self.current_date.isoformat()}", end_time.isoformat())

                self.current_date += timedelta(days=1)

                self.day_btn.config(text="Начать день")
                self.refresh_task_list()

                messagebox.showinfo("День завершен", f"День завершен в {end_time.strftime('%H:%M')}")
    def toggle_day_state(self):
        """Переключение состояния дня"""
        if self.day_started:
            self.end_day()
        else:
            self.start_day()


    def show_backlog(self):
        """Показать бэклог с расширенной информацией"""
        backlog_window = tk.Toplevel(self.root)
        backlog_window.title("Бэклог задач")
        backlog_window.geometry("800x600")

        ttk.Label(backlog_window, text="Бэклог задач",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Получение задач из бэклога
        backlog_tasks = self.db.get_tasks(include_backlog=True)
        backlog_tasks = [t for t in backlog_tasks if not t.date_scheduled]

        if not backlog_tasks:
            ttk.Label(backlog_window, text="Нет задач в бэклоге").pack(expand=True)
            return

        # Группировка по типам
        from modules.utils import TaskUtils
        task_types = self.db.get_task_types()
        grouped_tasks = TaskUtils.group_tasks_by_type(backlog_tasks, task_types)

        # Notebook для типов задач
        types_notebook = ttk.Notebook(backlog_window)
        types_notebook.pack(fill='both', expand=True, padx=10, pady=10)

        for type_name, tasks in grouped_tasks.items():
            # Фрейм для типа
            type_frame = ttk.Frame(types_notebook)
            types_notebook.add(type_frame, text=f"{type_name} ({len(tasks)})")

            # Список задач
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

            # Отображение задач с расширенной информацией
            for task in tasks:
                task_frame = ttk.Frame(scrollable_frame, relief='solid', bd=1)
                task_frame.pack(fill='x', pady=2, padx=2)

                # Заголовок с приоритетом
                header_frame = ttk.Frame(task_frame)
                header_frame.pack(fill='x', padx=5, pady=2)

                # Индикаторы
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
                           command=lambda t=task: self.move_to_today(t, backlog_window)).pack(side='left', padx=(0, 5))
                ttk.Button(btn_frame, text="Редактировать",
                           command=lambda t=task: self.edit_task_from_backlog(t, backlog_window)).pack(side='left',
                                                                                                       padx=(0, 5))
                ttk.Button(btn_frame, text="Удалить",
                           command=lambda t=task: self.delete_from_backlog(t, backlog_window)).pack(side='right')

        # Кнопка создания новой задачи в бэклог
        ttk.Button(backlog_window, text="+ Новая задача в бэклог",
                   command=lambda: self.create_backlog_task(backlog_window)).pack(pady=10)

    def move_to_today(self, task: Task, parent_window):
        """Перемещение задачи в сегодняшний день"""
        task.date_scheduled = self.current_date.isoformat()
        self.db.save_task(task)
        self.refresh_task_list()
        parent_window.destroy()
        messagebox.showinfo("Успех", f"Задача '{task.title}' перемещена в сегодняшние задачи")

    def edit_task_from_backlog(self, task: Task, parent_window):
        """Редактирование задачи из бэклога"""
        dialog = TaskEditDialog(parent_window, self, task)
        if dialog.result:
            parent_window.destroy()
            self.show_backlog()

    def delete_from_backlog(self, task: Task, parent_window):
        """Удаление задачи из бэклога"""
        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
            self.db.delete_task(task.id)
            parent_window.destroy()
            self.show_backlog()

    def create_backlog_task(self, parent_window):
        """Создание новой задачи в бэклог"""
        dialog = TaskEditDialog(parent_window, self)
        if dialog.result:
            parent_window.destroy()
            self.show_backlog()

    def go_to_date(self, target_date: date):
        """Переход к указанной дате"""
        old_date = self.current_date
        self.current_date = target_date

        # Обновляем интерфейс
        self.refresh_task_list()
        self.update_datetime()

        # Показываем информацию о переходе
        if target_date == date.today():
            msg = "Переход к сегодняшнему дню"
        elif target_date < date.today():
            msg = f"Переход к прошедшему дню: {target_date.strftime('%d.%m.%Y')}"
        else:
            msg = f"Переход к будущему дню: {target_date.strftime('%d.%m.%Y')}"

        messagebox.showinfo("Переход к дню", msg)

    def create_new_task_for_date(self, target_date: date):
        """Создание новой задачи для указанной даты"""
        new_task = Task()
        new_task.date_scheduled = target_date.isoformat()
        new_task.title = f"Новая задача на {target_date.strftime('%d.%m.%Y')}"

        new_task.id = self.db.save_task(new_task)
        return new_task

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

        # Русские названия дней недели и месяцев
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

        weekday = weekdays[self.current_date.weekday()]
        month = months[self.current_date.month - 1]

        date_str = f"{weekday}, {self.current_date.day} {month} {self.current_date.year}"
        time_str = now.strftime("%H:%M:%S")

        # Показываем текущую дату, а не обязательно сегодняшнюю
        if self.current_date == date.today():
            self.datetime_label.config(text=f"{date_str} | {time_str}")
        else:
            self.datetime_label.config(text=f"{date_str} (просмотр)")

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