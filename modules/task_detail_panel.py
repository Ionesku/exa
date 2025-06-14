# -*- coding: utf-8 -*-
"""
Task Manager - Панель деталей задачи (исправленная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .task_models import Task
from .colors import UI_COLORS


class TaskDetailPanel:
    """Панель отображения деталей задачи"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.current_task = None
        self.is_editing = False
        self.setup_panel()

    def setup_panel(self):
        """Создание панели деталей"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Детали задачи")
        self.main_frame.pack(side='bottom', fill='x', padx=5, pady=(5, 0))

        # Основной контейнер
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Левая часть - информация
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True)

        # Название
        ttk.Label(left_frame, text="Название:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(left_frame, textvariable=self.title_var, state='readonly')
        self.title_entry.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=2)

        # Содержание
        ttk.Label(left_frame, text="Содержание:").grid(row=1, column=0, sticky='nw', pady=2)
        # Фрейм для Text виджета
        content_text_frame = ttk.Frame(left_frame)
        content_text_frame.grid(row=1, column=1, sticky='ew', padx=(5, 0), pady=2)
        
        # Используем Text widget для многострочного содержания
        self.content_text = tk.Text(content_text_frame, height=3, width=40, state='disabled',
                                   bg='#f0f0f0', relief='groove', bd=1)
        self.content_text.pack(fill='both', expand=True)

        # Параметры
        params_frame = ttk.Frame(left_frame)
        params_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)

        ttk.Label(params_frame, text="Важность:").grid(row=0, column=0, padx=5)
        self.importance_var = tk.IntVar()
        self.importance_spin = ttk.Spinbox(params_frame, from_=1, to=10,
                                           textvariable=self.importance_var,
                                           width=5, state='readonly')
        self.importance_spin.grid(row=0, column=1, padx=5)

        ttk.Label(params_frame, text="Срочность:").grid(row=0, column=2, padx=5)
        self.priority_var = tk.IntVar()
        self.priority_spin = ttk.Spinbox(params_frame, from_=1, to=10,
                                         textvariable=self.priority_var,
                                         width=5, state='readonly')
        self.priority_spin.grid(row=0, column=3, padx=5)

        ttk.Label(params_frame, text="Длительность:").grid(row=0, column=4, padx=5)
        self.duration_var = tk.IntVar()
        self.duration_spin = ttk.Spinbox(params_frame, from_=5, to=480,
                                         textvariable=self.duration_var,
                                         width=8, state='readonly')
        self.duration_spin.grid(row=0, column=5, padx=5)

        # Правая часть - кнопки
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='right', fill='y', padx=(10, 0))

        self.edit_btn = ttk.Button(right_frame, text="Редактировать",
                                   command=self.toggle_edit_mode)
        self.edit_btn.pack(pady=2)


        self.cancel_btn = ttk.Button(right_frame, text="Отмена",
                                     command=self.cancel_edit, state='disabled')
        self.cancel_btn.pack(pady=2)

        # Настройка растягивания
        left_frame.grid_columnconfigure(1, weight=1)

        # Начальное состояние
        self.show_no_task()

    def show_task(self, task: Task):
        """Отображение задачи"""
        self.current_task = task

        if task:
            self.title_var.set(task.title)
            
            # Обновляем Text widget
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, task.content)
            self.content_text.config(state='disabled')

            self.importance_var.set(task.importance)
            self.priority_var.set(task.priority)
            self.duration_var.set(task.duration)

            self.main_frame.config(text=f"Детали задачи: {task.title[:30]}...")
            self.edit_btn.config(state='normal')
        else:
            self.show_no_task()

    def show_no_task(self):
        """Отображение пустого состояния"""
        self.title_var.set("")
        
        # Очищаем Text widget
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state='disabled')

        self.importance_var.set(1)
        self.priority_var.set(5)
        self.duration_var.set(30)

        self.main_frame.config(text="Детали задачи - выберите задачу")
        self.edit_btn.config(state='disabled')

    def toggle_edit_mode(self):
        """Переключение режима редактирования"""
        if self.is_editing:
            self.save_changes()
        else:
            self.enter_edit_mode()

    def enter_edit_mode(self):
        """Вход в режим редактирования"""
        self.is_editing = True

        # Разблокируем поля
        self.title_entry.config(state='normal')
        self.content_text.config(state='normal', bg='white')
        self.importance_spin.config(state='normal')
        self.priority_spin.config(state='normal')
        self.duration_spin.config(state='normal')

        # Меняем кнопки
        self.edit_btn.config(text="Сохранить", state='normal')
        self.save_btn.config(state='normal')
        self.cancel_btn.config(state='normal')

    def exit_edit_mode(self):
        """Выход из режима редактирования"""
        self.is_editing = False

        # Блокируем поля
        self.title_entry.config(state='readonly')
        self.content_text.config(state='disabled', bg='#f0f0f0')
        self.importance_spin.config(state='readonly')
        self.priority_spin.config(state='readonly')
        self.duration_spin.config(state='readonly')

        # Меняем кнопки
        self.edit_btn.config(text="Редактировать")
        self.save_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')

    def save_changes(self):
        """Сохранение изменений"""
        if not self.current_task:
            return

        # Валидация
        if not self.title_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название не может быть пустым!")
            return

        # Сохраняем изменения
        self.current_task.title = self.title_var.get().strip()
        self.current_task.content = self.content_text.get(1.0, tk.END).strip()
        self.current_task.importance = self.importance_var.get()
        self.current_task.priority = self.priority_var.get()
        self.current_task.duration = self.duration_var.get()

        # Сохраняем в БД через сервис
        self.task_manager.task_service.update_task(self.current_task)

        self.exit_edit_mode()
        messagebox.showinfo("Успех", "Изменения сохранены!")

    def cancel_edit(self):
        """Отмена редактирования"""
        if self.current_task:
            self.show_task(self.current_task)
        self.exit_edit_mode()