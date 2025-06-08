#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - Основной файл приложения (рефакторинг)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from typing import Optional

# Импорт модулей
from modules import (
    Task, TaskType, DatabaseManager,
    get_priority_color, UI_COLORS,
    CompactQuadrantsWidget, TaskListWidget, TaskEditPanel,
    CalendarMixin, DragDropMixin
)


class TaskManager(DragDropMixin, CalendarMixin):
    """Основной класс приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("1000x700")  # Компактный размер
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
        """Настройка основной вкладки"""
        # Основной контейнер
        main_container = ttk.Frame(self.task_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Верхняя панель с информацией и кнопками
        self.setup_top_panel(main_container)

        # Средняя панель с квадрантами и задачами
        middle_panel = ttk.Frame(main_container)
        middle_panel.pack(fill='both', expand=True)

        # Создание компонентов интерфейса
        self.quadrants_widget = CompactQuadrantsWidget(middle_panel, self)
        self.task_list_widget = TaskListWidget(middle_panel, self)

        # Нижняя панель редактирования
        self.edit_panel = TaskEditPanel(main_container, self)

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

        for key, description in hotkeys:
            frame = ttk.Frame(hotkey_window)
            frame.pack(fill='x', padx=10, pady=2)
            ttk.Label(frame, text=key, font=('Arial', 10, 'bold')).pack(side='left')
            ttk.Label(frame, text=description).pack(side='left', padx=(20, 0))

    # Основные методы работы с задачами
    def create_new_task(self):
        """Создание новой задачи"""
        self.current_task = Task()
        self.load_task_to_editor(self.current_task)
        self.set_edit_mode(True)
        self.edit_panel.title_entry.focus()

    def load_task_to_editor(self, task: Task):
        """Загрузка задачи в редактор"""
        self.edit_panel.title_var.set(task.title)
        self.edit_panel.content_text.delete(1.0, tk.END)
        self.edit_panel.content_text.insert(1.0, task.content)
        self.edit_panel.importance_var.set(task.importance)
        self.edit_panel.duration_var.set(task.duration)
        self.edit_panel.has_duration_var.set(task.has_duration)
        self.edit_panel.priority_var.set(task.priority)
        self.edit_panel.toggle_duration()

        # Загрузка типов задач
        self.edit_panel.load_task_types()
        task_types = self.db.get_task_types()

        if task.task_type_id and task.task_type_id <= len(task_types):
            self.edit_panel.task_type_var.set(task_types[task.task_type_id - 1].name)
        else:
            if task_types:
                self.edit_panel.task_type_var.set(task_types[0].name)

        # Установка даты планирования
        if not task.date_scheduled:
            self.edit_panel.date_var.set("Бэклог")
        elif task.date_scheduled == self.current_date.isoformat():
            self.edit_panel.date_var.set("Сегодня")
        else:
            self.edit_panel.date_var.set("Другая дата...")
            try:
                task_date = datetime.strptime(task.date_scheduled, '%Y-%m-%d').date()
                self.edit_panel.custom_date_var.set(task_date.strftime('%d.%m.%Y'))
                self.edit_panel.custom_date_entry.config(state='normal')
            except:
                self.edit_panel.custom_date_var.set("")

    def save_current_task(self):
        """Сохранение текущей задачи"""
        if not self.current_task:
            return

        if not self.edit_panel.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название задачи не может быть пустым!")
            return

        # Получение типа задачи
        task_types = self.db.get_task_types()
        type_name = self.edit_panel.task_type_var.get()
        task_type_id = 1
        for t in task_types:
            if t.name == type_name:
                task_type_id = t.id
                break

        # Определение даты планирования
        date_option = self.edit_panel.date_var.get()
        if date_option == "Бэклог":
            date_scheduled = ""
        elif date_option == "Сегодня":
            date_scheduled = self.current_date.isoformat()
        elif date_option == "Другая дата...":
            try:
                custom_date_str = self.edit_panel.custom_date_var.get()
                custom_date = datetime.strptime(custom_date_str, '%d.%m.%Y').date()
                date_scheduled = custom_date.isoformat()
            except:
                messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
                return
        else:
            date_scheduled = self.current_date.isoformat()

        # Обновление данных задачи
        self.current_task.title = self.edit_panel.title_var.get().strip()
        self.current_task.content = self.edit_panel.content_text.get(1.0, tk.END).strip()
        self.current_task.importance = self.edit_panel.importance_var.get()
        self.current_task.duration = self.edit_panel.duration_var.get()
        self.current_task.has_duration = self.edit_panel.has_duration_var.get()
        self.current_task.priority = self.edit_panel.priority_var.get()
        self.current_task.task_type_id = task_type_id
        self.current_task.date_scheduled = date_scheduled

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
        self.edit_panel.title_var.set("")
        self.edit_panel.content_text.delete(1.0, tk.END)
        self.edit_panel.importance_var.set(1)
        self.edit_panel.duration_var.set(30)
        self.edit_panel.has_duration_var.set(False)
        self.edit_panel.priority_var.set(5)
        self.edit_panel.task_type_var.set("")
        self.edit_panel.date_var.set("Сегодня")
        self.edit_panel.custom_date_var.set("")
        self.edit_panel.toggle_duration()
        self.set_edit_mode(False)

    def toggle_edit_mode(self):
        """Переключение режима редактирования"""
        if self.current_task:
            current_mode = str(self.edit_panel.title_entry['state']) != 'disabled'
            self.set_edit_mode(not current_mode)

    def set_edit_mode(self, enabled: bool):
        """Установка режима редактирования"""
        self.edit_panel.set_edit_mode(enabled)

    def refresh_task_list(self):
        """Обновление списка задач"""
        # Очистка текущего списка
        self.task_list_widget.clear_tasks()

        # Получение задач только для текущей даты (не бэклог)
        date_str = self.current_date.isoformat()
        tasks = self.db.get_tasks(date_str, include_backlog=False)

        # Создание кнопок для задач
        for task in tasks:
            self.task_list_widget.add_task_button(task)

        # Обновление квадрантов
        self.refresh_quadrants(tasks)

        # Обновление области переработок
        self.refresh_overtime_area(tasks)

    def refresh_quadrants(self, tasks):
        """Обновление отображения квадрантов"""
        self.quadrants_widget.clear_quadrants()

        # Размещение задач в квадрантах
        for task in tasks:
            if 1 <= task.quadrant <= 4:
                self.quadrants_widget.add_task_to_quadrant(task, task.quadrant)

    def refresh_overtime_area(self, tasks):
        """Обновление области переработок"""
        # TODO: Реализовать область переработок
        pass

    def select_task(self, task: Task):
        """Выбор задачи для редактирования"""
        self.current_task = task
        self.load_task_to_editor(task)
        self.set_edit_mode(False)

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
            self.quadrants_widget.update_time_labels(start_hour)

            self.start_day_btn.config(text="День начат", state='disabled')
            self.end_day_btn.config(state='normal')

            messagebox.showinfo("День начат", f"День начат в {self.day_start_time.strftime('%H:%M')}")

    def end_day(self):
        """Завершение дня"""
        if self.day_started:
            if messagebox.askyesno("Завершение дня", "Завершить текущий день?"):
                self.day_started = False

                end_time = datetime.now().time()
                self.db.save_setting(f"day_end_{self.current_date.isoformat()}", end_time.isoformat())

                self.current_date += timedelta(days=1)

                self.start_day_btn.config(text="Начать день", state='normal')
                self.end_day_btn.config(state='disabled')

                self.refresh_task_list()

                messagebox.showinfo("День завершен", f"День завершен в {end_time.strftime('%H:%M')}")

    def show_backlog(self):
        """Показать бэклог"""
        backlog_window = tk.Toplevel(self.root)
        backlog_window.title("Бэклог задач")
        backlog_window.geometry("700x500")

        ttk.Label(backlog_window, text="Бэклог задач",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Получение задач из бэклога (без установленной даты)
        backlog_tasks = self.db.get_tasks(include_backlog=True)
        backlog_tasks = [t for t in backlog_tasks if not t.date_scheduled]

        if not backlog_tasks:
            ttk.Label(backlog_window, text="Нет задач в бэклоге").pack(expand=True)
            return

        # Прокручиваемый список задач
        canvas_frame = ttk.Frame(backlog_window)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

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

        # Список задач
        for task in backlog_tasks:
            task_frame = ttk.Frame(scrollable_frame)
            task_frame.pack(fill='x', pady=2)

            # Индикатор приоритета
            priority_color = get_priority_color(task.priority)
            priority_label = tk.Label(task_frame, text="●", font=('Arial', 12), fg=priority_color)
            priority_label.pack(side='left', padx=(0, 5))

            # Название задачи
            ttk.Button(
                task_frame,
                text=task.title,
                command=lambda t=task: self.move_to_today(t, backlog_window)
            ).pack(side='left', fill='x', expand=True)

            # Кнопка удаления
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
            self.show_backlog()

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
        date_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%H:%M:%S")
        self.datetime_label.config(text=f"{date_str} | {time_str}")

        self.root.after(1000, self.update_datetime)

    def load_data(self):
        """Загрузка данных при запуске"""
        self.edit_panel.load_task_types()
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