# -*- coding: utf-8 -*-
"""
Task Manager - Диалог редактирования задачи (переработанный)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

from .task_models import Task
from .task_type_dialog import TaskTypeDialog
from .colors import get_priority_color

logger = logging.getLogger(__name__)


class TaskEditDialog:
    """Диалог редактирования задачи"""

    def __init__(self, parent, task_manager, task=None):
        self.task_manager = task_manager
        self.task = task or Task()
        self.is_new_task = task is None or task.id == 0
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Новая задача" if self.is_new_task else "Редактирование задачи")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.load_task_data()
        self.center_window()

    def setup_ui(self):
        """Создание интерфейса"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Название
        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var)
        self.title_entry.pack(fill='x', pady=(0, 10))
        self.title_entry.focus()

        # Содержание
        ttk.Label(main_frame, text="Содержание:").pack(anchor='w', pady=(0, 5))
        self.content_text = tk.Text(main_frame, height=4)
        self.content_text.pack(fill='x', pady=(0, 10))

        # Параметры
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill='x', pady=(0, 10))

        # Левая колонка
        left_frame = ttk.Frame(params_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Важность
        ttk.Label(left_frame, text="Важность (1-10):").pack(anchor='w')
        self.importance_var = tk.IntVar(value=1)
        importance_frame = ttk.Frame(left_frame)
        importance_frame.pack(anchor='w', pady=(0, 10))
        
        ttk.Spinbox(importance_frame, from_=1, to=10, textvariable=self.importance_var,
                    width=5).pack(side='left')
        ttk.Label(importance_frame, text="(1 - низкая, 10 - высокая)",
                  font=('Arial', 8)).pack(side='left', padx=(10, 0))

        # Срочность
        ttk.Label(left_frame, text="Срочность (1-10):").pack(anchor='w')
        priority_frame = ttk.Frame(left_frame)
        priority_frame.pack(anchor='w', pady=(0, 10))

        self.priority_var = tk.IntVar(value=5)
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.priority_var,
                    width=5).pack(side='left', padx=(0, 5))
        self.priority_color_label = tk.Label(priority_frame, text="●", font=('Arial', 16))
        self.priority_color_label.pack(side='left')

        # Правая колонка
        right_frame = ttk.Frame(params_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        # Длительность
        self.has_duration_var = tk.BooleanVar()
        duration_check = ttk.Checkbutton(right_frame, text="Установить длительность",
                                         variable=self.has_duration_var,
                                         command=self.toggle_duration)
        duration_check.pack(anchor='w')

        duration_frame = ttk.Frame(right_frame)
        duration_frame.pack(anchor='w', pady=(0, 10))

        self.duration_var = tk.IntVar(value=30)
        self.duration_spin = ttk.Spinbox(duration_frame, from_=5, to=480,
                                         textvariable=self.duration_var, 
                                         width=8, state='disabled')
        self.duration_spin.pack(side='left', padx=(0, 5))
        ttk.Label(duration_frame, text="минут").pack(side='left')

        # Тип задачи
        ttk.Label(right_frame, text="Тип задачи:").pack(anchor='w')
        type_frame = ttk.Frame(right_frame)
        type_frame.pack(anchor='w', pady=(0, 10))

        self.task_type_var = tk.StringVar()
        self.task_type_combo = ttk.Combobox(type_frame, textvariable=self.task_type_var,
                                            width=15, state='readonly')
        self.task_type_combo.pack(side='left', padx=(0, 5))
        ttk.Button(type_frame, text="+", width=3,
                   command=self.add_task_type).pack(side='left')

        # Планирование
        planning_frame = ttk.LabelFrame(main_frame, text="Планирование")
        planning_frame.pack(fill='x', pady=(10, 10))

        plan_content = ttk.Frame(planning_frame)
        plan_content.pack(fill='x', padx=10, pady=10)

        ttk.Label(plan_content, text="Сохранить в:").pack(side='left', padx=(0, 10))
        
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(plan_content, textvariable=self.date_var,
                                       values=self.get_date_options(),
                                       state='readonly', width=15)
        self.date_combo.pack(side='left', padx=(0, 10))

        self.custom_date_var = tk.StringVar()
        self.custom_date_entry = ttk.Entry(plan_content, textvariable=self.custom_date_var,
                                           state='disabled', width=12)
        self.custom_date_entry.pack(side='left')

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        save_text = "Создать" if self.is_new_task else "Сохранить"
        ttk.Button(btn_frame, text=save_text, command=self.save_task).pack(side='right', padx=(0, 10))

        # Привязка событий
        self.priority_var.trace('w', self.update_priority_color)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_option_selected)

        # Инициализация
        self.update_priority_color()
        self.load_task_types()

    def get_date_options(self):
        """Получение опций даты"""
        options = ["Бэклог", "Сегодня", "Другая дата..."]
        
        # Добавляем последний выбор если он отличается
        last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")
        if last_choice not in options:
            options.insert(1, last_choice)
            
        return options

    def load_task_data(self):
        """Загрузка данных задачи"""
        if not self.is_new_task:
            # Загружаем данные существующей задачи
            self.title_var.set(self.task.title)
            self.content_text.insert(1.0, self.task.content)
            self.importance_var.set(self.task.importance)
            self.priority_var.set(self.task.priority)
            self.has_duration_var.set(self.task.has_duration)
            self.duration_var.set(self.task.duration)
            
            # Определяем где сохранена задача
            if not self.task.date_scheduled:
                self.date_var.set("Бэклог")
            elif self.task.date_scheduled == self.task_manager.current_date.isoformat():
                self.date_var.set("Сегодня")
            else:
                self.date_var.set("Другая дата...")
                try:
                    task_date = datetime.strptime(self.task.date_scheduled, '%Y-%m-%d').date()
                    self.custom_date_var.set(task_date.strftime('%d.%m.%Y'))
                    self.custom_date_entry.config(state='normal')
                except:
                    logger.error(f"Failed to parse task date: {self.task.date_scheduled}")
        else:
            # Для новой задачи
            if hasattr(self.task, 'date_scheduled') and self.task.date_scheduled:
                # Если дата предустановлена (например, из календаря)
                if self.task.date_scheduled == self.task_manager.current_date.isoformat():
                    self.date_var.set("Сегодня")
                else:
                    self.date_var.set("Другая дата...")
                    try:
                        task_date = datetime.strptime(self.task.date_scheduled, '%Y-%m-%d').date()
                        self.custom_date_var.set(task_date.strftime('%d.%m.%Y'))
                        self.custom_date_entry.config(state='normal')
                    except:
                        pass
            else:
                # Используем последний выбор или "Сегодня"
                last_choice = self.task_manager.db.get_setting("last_save_location", "Сегодня")
                self.date_var.set(last_choice)
        
        self.toggle_duration()

    def toggle_duration(self):
        """Переключение доступности поля длительности"""
        state = 'normal' if self.has_duration_var.get() else 'disabled'
        self.duration_spin.config(state=state)

    def update_priority_color(self, *args):
        """Обновление цвета индикатора приоритета"""
        try:
            priority = self.priority_var.get()
            color = get_priority_color(priority)
            self.priority_color_label.config(fg=color)
        except:
            pass

    def on_date_option_selected(self, event=None):
        """Обработка выбора опции даты"""
        selected = self.date_var.get()
        if selected == "Другая дата...":
            self.custom_date_entry.config(state='normal')
            if not self.custom_date_var.get():
                today = datetime.now().date()
                self.custom_date_var.set(today.strftime('%d.%m.%Y'))
        else:
            self.custom_date_entry.config(state='disabled')
            self.custom_date_var.set("")

    def load_task_types(self):
        """Загрузка типов задач"""
        task_types = self.task_manager.get_task_types()
        type_names = [t.name for t in task_types]
        self.task_type_combo['values'] = type_names

        if task_types:
            if self.task.task_type_id and self.task.task_type_id <= len(task_types):
                # Устанавливаем тип существующей задачи
                self.task_type_var.set(task_types[self.task.task_type_id - 1].name)
            else:
                # По умолчанию первый тип
                self.task_type_var.set(type_names[0])

    def add_task_type(self):
        """Добавление нового типа задачи"""
        dialog = TaskTypeDialog(self.dialog, self.task_manager.db)
        if dialog.result:
            # Обновляем кеш типов
            self.task_manager.get_task_types(force_refresh=True)
            self.load_task_types()
            self.task_type_var.set(dialog.result.name)

    def save_task(self):
        """Сохранение задачи"""
        # Валидация
        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название задачи не может быть пустым!")
            return

        # Определяем тип задачи
        task_types = self.task_manager.get_task_types()
        type_name = self.task_type_var.get()
        task_type_id = 1
        for t in task_types:
            if t.name == type_name:
                task_type_id = t.id
                break

        # Определяем дату
        date_option = self.date_var.get()
        if date_option == "Бэклог":
            date_scheduled = ""
        elif date_option == "Сегодня":
            date_scheduled = self.task_manager.current_date.isoformat()
        elif date_option == "Другая дата...":
            try:
                custom_date_str = self.custom_date_var.get()
                custom_date = datetime.strptime(custom_date_str, '%d.%m.%Y').date()
                date_scheduled = custom_date.isoformat()
            except:
                messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
                return
        else:
            # По умолчанию сегодня
            date_scheduled = self.task_manager.current_date.isoformat()

        # Сохраняем выбор места сохранения
        if self.is_new_task and not hasattr(self.task, 'date_scheduled'):
            self.task_manager.db.save_setting("last_save_location", date_option)

        # Обновляем объект задачи
        self.task.title = self.title_var.get().strip()
        self.task.content = self.content_text.get(1.0, tk.END).strip()
        self.task.importance = self.importance_var.get()
        self.task.priority = self.priority_var.get()
        self.task.has_duration = self.has_duration_var.get()
        self.task.duration = self.duration_var.get()
        self.task.task_type_id = task_type_id
        self.task.date_scheduled = date_scheduled

        # Сохраняем через сервис
        try:
            if self.is_new_task:
                logger.info(f"Creating new task: {self.task.title}")
                self.result = self.task_manager.task_service.create_task(self.task)
            else:
                logger.info(f"Updating task: {self.task.title}")
                self.result = self.task_manager.task_service.update_task(self.task)
            
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачу: {str(e)}")

    def cancel(self):
        """Отмена диалога"""
        self.dialog.destroy()

    def center_window(self):
        """Центрирование окна"""
        self.dialog.update_idletasks()
        
        # Получаем размеры экрана
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # Получаем размеры окна
        window_width = self.dialog.winfo_width()
        window_height = self.dialog.winfo_height()
        
        # Вычисляем позицию
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.dialog.geometry(f'+{x}+{y}')