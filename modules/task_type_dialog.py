# -*- coding: utf-8 -*-
"""
Task Manager - Диалог создания типа задачи
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from .task_models import TaskType


class TaskTypeDialog:
    """Диалог создания типа задачи"""

    def __init__(self, parent, db_manager):
        self.db = db_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Новый тип задачи")
        self.dialog.geometry("350x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        """Создание интерфейса"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Название
        ttk.Label(main_frame, text="Название:").pack(anchor='w', pady=(0, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var).pack(fill='x', pady=(0, 10))

        # Цвет
        color_frame = ttk.Frame(main_frame)
        color_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(color_frame, text="Цвет:").pack(side='left')
        self.color_var = tk.StringVar(value="#2196F3")
        ttk.Entry(color_frame, textvariable=self.color_var, width=8).pack(side='left', padx=(10, 5))

        self.color_preview = tk.Label(color_frame, text="  ", bg=self.color_var.get(),
                                      relief='solid', bd=1)
        self.color_preview.pack(side='left', padx=(0, 5))

        ttk.Button(color_frame, text="Выбрать", command=self.choose_color).pack(side='left')

        # Описание
        ttk.Label(main_frame, text="Описание:").pack(anchor='w', pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=3)
        self.description_text.pack(fill='both', expand=True, pady=(0, 10))

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side='right')
        ttk.Button(btn_frame, text="Создать", command=self.create_type).pack(side='right', padx=(0, 5))

        # Привязка событий
        self.color_var.trace('w', self.update_color_preview)

    def choose_color(self):
        """Выбор цвета"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])

    def update_color_preview(self, *args):
        """Обновление предпросмотра цвета"""
        try:
            self.color_preview.config(bg=self.color_var.get())
        except:
            pass

    def create_type(self):
        """Создание типа задачи"""
        if not self.name_var.get().strip():
            messagebox.showwarning("Предупреждение", "Название не может быть пустым!")
            return

        task_type = TaskType(
            name=self.name_var.get().strip(),
            color=self.color_var.get(),
            description=self.description_text.get(1.0, tk.END).strip()
        )

        task_type.id = self.db.save_task_type(task_type)
        self.result = task_type
        self.dialog.destroy()

    def cancel(self):
        """Отмена"""
        self.dialog.destroy()

    def center_window(self):
        """Центрирование окна"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f'+{x}+{y}')