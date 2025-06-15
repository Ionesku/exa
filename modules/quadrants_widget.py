# -*- coding: utf-8 -*-
"""
Task Manager - Виджет квадрантов с инкрементальными обновлениями
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import logging

from .task_models import Task
from .colors import get_priority_color, get_completed_color, QUADRANT_COLORS
from .incremental_updater import IncrementalUpdater, SmartUpdateMixin

logger = logging.getLogger(__name__)


class QuadrantsWidget(SmartUpdateMixin):
    """Виджет квадрантов с оптимизированными обновлениями"""

    def __init__(self, parent, task_manager):
        super().__init__()
        self.parent = parent
        self.task_manager = task_manager
        self.quadrants = {}
        self.time_labels = {}
        self.selected_task: Optional[Task] = None
        self.drag_data = {"task": None, "widget": None}
        self.updater = IncrementalUpdater()
        
        # Кеш для отслеживания состояния
        self._task_widgets_cache = {}  # task_id -> widget
        self._current_tasks = {}  # quadrant -> set of task_ids
        
        # Для контекстного меню
        self.context_menu = None
        self.menu_visible = False
        
        self.setup_quadrants()

    def setup_context_menu(self, current_quadrant: int = None):
        """Создание контекстного меню для задач"""
        if self.context_menu:
            self.context_menu.destroy()
            
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        
        # Добавляем пункты квадрантов, исключая текущий
        for i in range(1, 5):
            if i != current_quadrant:
                self.context_menu.add_command(
                    label=f"В {i}-й квадрант", 
                    command=lambda q=i: self.move_selected_to_quadrant(q)
                )
        
        self.context_menu.add_separator()
        
        # Пункт "В список задач" только если задача не в списке
        if current_quadrant != 0:
            self.context_menu.add_command(
                label="В список задач", 
                command=lambda: self.move_selected_to_quadrant(0)
            )
        
        self.context_menu.add_command(
            label="В бэклог", 
            command=self.move_selected_to_backlog
        )
        
        self.context_menu.add_separator()
        
        # Добавляем пункт "Выполнено"
        if self.selected_task:
            if self.selected_task.is_completed:
                self.context_menu.add_command(
                    label="Отменить выполнение",
                    command=lambda: self.toggle_task_completion(False)
                )
            else:
                self.context_menu.add_command(
                    label="✓ Выполнено",
                    command=lambda: self.toggle_task_completion(True)
                )
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_quadrants(self):
        """Создание квадрантов"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Планирование")
        
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)

        quad_configs = [
            (0, 0, 1, "09:00", QUADRANT_COLORS[1], "Квадрант 1"),
            (0, 1, 2, "12:00", QUADRANT_COLORS[2], "Квадрант 2"),
            (1, 1, 3, "15:00", QUADRANT_COLORS[3], "Квадрант 3"),
            (1, 0, 4, "18:00", QUADRANT_COLORS[4], "Квадрант 4")
        ]

        for row, col, quad_id, time_text, color, title in quad_configs:
            self._create_quadrant(row, col, quad_id, time_text, color, title)
            self._current_tasks[quad_id] = set()

    def _create_quadrant(self, row: int, col: int, quad_id: int, time_text: str, color: str, title: str):
        """Создание одного квадранта"""
        quad_frame = tk.Frame(self.grid_frame, bg=color, relief='solid', bd=2)
        quad_frame.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

        quad_frame.bind("<Enter>", lambda e, q=quad_id: self._on_quadrant_enter(e, q))
        quad_frame.bind("<Leave>", lambda e, q=quad_id: self._on_quadrant_leave(e, q))
        quad_frame.bind("<ButtonRelease-1>", lambda e, q=quad_id: self._on_quadrant_drop(e, q))

        header_frame = tk.Frame(quad_frame, bg=color)
        header_frame.pack(fill='x', padx=5, pady=(5, 0))

        title_label = tk.Label(header_frame, text=title,
                              bg=color, font=('Arial', 9, 'bold'))
        title_label.pack(side='left')

        if quad_id == 4:
            time_label = tk.Label(header_frame, text="18:00 - 21:00",
                                 bg=color, font=('Arial', 10, 'bold'))
        else:
            time_label = tk.Label(header_frame, text=time_text,
                                 bg=color, font=('Arial', 10, 'bold'))
        
        if quad_id == 1:
            time_label.config(cursor='hand2')
            time_label.bind('<Button-1>', lambda e: self.edit_start_time())
        
        time_label.pack(side='left', padx=(10, 0))

        info_label = tk.Label(header_frame, text="",
                             bg=color, font=('Arial', 9))
        info_label.pack(side='right')

        task_container = tk.Frame(quad_frame, bg='white')
        task_container.pack(fill='both', expand=True, padx=5, pady=5)

        inner_table = tk.Frame(task_container, bg='white')
        inner_table.pack(fill='both', expand=True)

        task_container.bind("<ButtonRelease-1>", lambda e, q=quad_id: self._on_quadrant_drop(e, q))

        # Сохраняем пустой заполнитель
        empty_label = tk.Label(inner_table, text="Перетащите задачи сюда",
                              bg='white', fg='gray', font=('Arial', 10))
        empty_label.pack(expand=True)

        self.quadrants[quad_id] = {
            'frame': quad_frame,
            'table': inner_table,
            'container': task_container,
            'time_label': time_label,
            'info_label': info_label,
            'tasks': [],
            'color': color,
            'task_widgets': {},
            'empty_label': empty_label
        }

        self.time_labels[quad_id] = time_label

    def update_quadrants(self, quadrant_tasks: Dict[int, List[Task]]):
        """Инкрементальное обновление квадрантов"""
        logger.debug("Starting incremental quadrant update")
        
        for quad_id in range(1, 5):
            new_tasks = quadrant_tasks.get(quad_id, [])
            self._update_single_quadrant(quad_id, new_tasks)

    def _update_single_quadrant(self, quad_id: int, new_tasks: List[Task]):
        """Обновление одного квадранта только при необходимости"""
        if quad_id not in self.quadrants:
            return
        
        quad_data = self.quadrants[quad_id]
        current_task_ids = self._current_tasks[quad_id]
        new_task_ids = {t.id for t in new_tasks}
        
        # Определяем изменения
        added_ids = new_task_ids - current_task_ids
        removed_ids = current_task_ids - new_task_ids
        common_ids = current_task_ids & new_task_ids
        
        # Нет изменений - не обновляем
        if not added_ids and not removed_ids and not any(self._task_changed(t) for t in new_tasks if t.id in common_ids):
            return
        
        logger.debug(f"Updating quadrant {quad_id}: +{len(added_ids)} -{len(removed_ids)} ~{len(common_ids)}")
        
        # Убираем пустой заполнитель если есть задачи
        if new_tasks and quad_data['empty_label'].winfo_exists():
            quad_data['empty_label'].pack_forget()
        
        # Удаляем виджеты удаленных задач
        for task_id in removed_ids:
            if task_id in quad_data['task_widgets']:
                widget = quad_data['task_widgets'][task_id]
                self.queue_update(self._remove_task_widget, widget, task_id, quad_id)
        
        # Обновляем существующие задачи
        for task in new_tasks:
            if task.id in common_ids:
                if self._task_changed(task):
                    self.queue_update(self._update_task_widget, task, quad_id)
        
        # Добавляем новые задачи
        for task in new_tasks:
            if task.id in added_ids:
                self.queue_update(self._add_task_widget, task, quad_id)
        
        # Обновляем layout и информацию
        self.queue_update(self._update_quadrant_layout, quad_id, new_tasks)
        
        # Обновляем кеш
        self._current_tasks[quad_id] = new_task_ids
        quad_data['tasks'] = new_tasks

    def _task_changed(self, task: Task) -> bool:
        """Проверка, изменилась ли задача"""
        if task.id not in self._task_widgets_cache:
            return True
        
        cached_widget = self._task_widgets_cache[task.id]
        if not hasattr(cached_widget, '_task_state'):
            return True
        
        old_state = cached_widget._task_state
        new_state = (task.title, task.is_completed, task.priority, task.has_duration, task.duration)
        
        return old_state != new_state

    def _remove_task_widget(self, widget: tk.Widget, task_id: int, quad_id: int):
        """Удаление виджета задачи с анимацией"""
        if widget.winfo_exists():
            # Простое удаление (можно добавить fade-out анимацию)
            widget.destroy()
        
        # Очистка из кешей
        if task_id in self.quadrants[quad_id]['task_widgets']:
            del self.quadrants[quad_id]['task_widgets'][task_id]
        if task_id in self._task_widgets_cache:
            del self._task_widgets_cache[task_id]

    def _update_task_widget(self, task: Task, quad_id: int):
        """Обновление существующего виджета задачи"""
        if task.id not in self.quadrants[quad_id]['task_widgets']:
            return
        
        widget = self.quadrants[quad_id]['task_widgets'][task.id]
        if not widget.winfo_exists():
            return
        
        # Обновляем цвет если изменился приоритет или статус
        new_color = get_completed_color() if task.is_completed else get_priority_color(task.priority)
        current_color = widget.cget('bg')
        
        if current_color != new_color:
            # Можно добавить анимацию изменения цвета
            widget.config(bg=new_color)
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=new_color)
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            subchild.config(bg=new_color)
        
        # Обновляем текст
        for child in widget.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label) and hasattr(subchild, '_is_title'):
                        title_text = task.title[:20] + "..." if len(task.title) > 20 else task.title
                        if task.is_completed:
                            title_text = f"✓ {title_text}"
                        subchild.config(text=title_text)
                    elif isinstance(subchild, tk.Label) and hasattr(subchild, '_is_duration'):
                        if task.has_duration:
                            subchild.config(text=f"{task.duration}м")
                            subchild.pack()
                        else:
                            subchild.pack_forget()
        
        # Сохраняем новое состояние
        widget._task_state = (task.title, task.is_completed, task.priority, task.has_duration, task.duration)

    def _add_task_widget(self, task: Task, quad_id: int):
        """Добавление нового виджета задачи"""
        table = self.quadrants[quad_id]['table']
        
        # Создаем виджет
        task_widget = self._create_task_widget(table, task, quad_id)
        
        # Сохраняем в кеши
        self.quadrants[quad_id]['task_widgets'][task.id] = task_widget
        self._task_widgets_cache[task.id] = task_widget
        
        # Сохраняем состояние
        task_widget._task_state = (task.title, task.is_completed, task.priority, task.has_duration, task.duration)

    def _update_quadrant_layout(self, quad_id: int, tasks: List[Task]):
        """Обновление layout квадранта"""
        quad_data = self.quadrants[quad_id]
        table = quad_data['table']
        
        if not tasks:
            # Показываем пустой заполнитель
            if not quad_data['empty_label'].winfo_manager():
                quad_data['empty_label'].pack(expand=True)
            quad_data['info_label'].config(text="")
            return
        
        # Скрываем пустой заполнитель
        if quad_data['empty_label'].winfo_manager():
            quad_data['empty_label'].pack_forget()
        
        # Вычисляем оптимальную сетку
        num_tasks = len(tasks)
        if num_tasks <= 4:
            cols = 2
        elif num_tasks <= 9:
            cols = 3
        else:
            cols = 4
        
        # Размещаем виджеты в сетке
        for i, task in enumerate(tasks):
            if task.id in quad_data['task_widgets']:
                widget = quad_data['task_widgets'][task.id]
                if widget.winfo_exists():
                    row = i // cols
                    col = i % cols
                    widget.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
        
        # Настройка весов сетки
        for i in range((num_tasks + cols - 1) // cols):
            table.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            table.grid_columnconfigure(i, weight=1)
        
        # Обновляем информацию
        total_duration = sum(t.duration if t.has_duration else 30 for t in tasks)
        hours = total_duration // 60
        minutes = total_duration % 60
        info_text = f"Задач: {len(tasks)} | {hours}ч {minutes}м"
        
        quad_data['info_label'].config(
            text=info_text,
            fg='red' if total_duration > 180 else 'black'
        )

    def _create_task_widget(self, parent, task: Task, quadrant: int) -> tk.Frame:
        """Создание виджета для одной задачи (без чекбокса)"""
        bg_color = get_completed_color() if task.is_completed else get_priority_color(task.priority)
        
        task_frame = tk.Frame(parent, bg=bg_color, relief='raised', bd=1)

        content_frame = tk.Frame(task_frame, bg=bg_color)
        content_frame.pack(fill='both', expand=True, padx=3, pady=3)

        title_text = task.title[:20] + "..." if len(task.title) > 20 else task.title
        if task.is_completed:
            title_text = f"✓ {title_text}"
            
        title_label = tk.Label(
            content_frame, 
            text=title_text,
            bg=bg_color,
            fg='white', 
            font=('Arial', 9, 'bold'),
            wraplength=100, 
            justify='center'
        )
        title_label._is_title = True  # Маркер для идентификации
        title_label.pack(expand=True, pady=(5, 2))

        # Длительность
        duration_label = tk.Label(
            content_frame, 
            text=f"{task.duration}м",
            bg=bg_color,
            fg='white', 
            font=('Arial', 8)
        )
        duration_label._is_duration = True  # Маркер для идентификации
        
        if task.has_duration:
            duration_label.pack()

        # События
        for widget in [task_frame, content_frame, title_label]:
            widget.bind("<Button-1>", lambda e, t=task: self._on_task_click(e, t))
            widget.bind("<B1-Motion>", lambda e, t=task, w=task_frame: self._on_task_drag(e, t, w))
            widget.bind("<ButtonRelease-1>", lambda e: self._on_task_release(e))
            widget.bind("<Button-3>", lambda e, t=task, q=quadrant: self._show_context_menu(e, t, q))

        return task_frame

    def _global_right_click_handler(self, event):
        """Глобальный обработчик правого клика для закрытия меню"""
        if self.menu_visible:
            # Проверяем, что клик был не на самом меню
            try:
                widget_under_mouse = event.widget.winfo_containing(event.x_root, event.y_root)
                if widget_under_mouse != self.context_menu:
                    self.hide_context_menu()
                    return "break"
            except:
                self.hide_context_menu()

    def _global_left_click_handler(self, event):
        """Глобальный обработчик левого клика для закрытия меню"""
        if self.menu_visible:
            # Проверяем, что клик был не на самом меню
            try:
                # Получаем виджет под курсором
                widget = event.widget
                # Проверяем, не является ли это меню или его дочерним элементом
                menu_clicked = False
                try:
                    # Проверяем, если виджет - это само меню
                    if str(widget) == str(self.context_menu):
                        menu_clicked = True
                    # Проверяем родителей виджета
                    parent = widget
                    while parent:
                        if str(parent) == str(self.context_menu):
                            menu_clicked = True
                            break
                        try:
                            parent = parent.master
                        except:
                            break
                except:
                    pass
                
                if not menu_clicked:
                    self.hide_context_menu()
            except:
                self.hide_context_menu()

    def hide_context_menu(self):
        """Скрыть контекстное меню"""
        if self.context_menu and self.menu_visible:
            self.context_menu.unpost()
            self.menu_visible = False
            # Убираем обработчик клика
            try:
                self.task_manager.root.unbind("<Button-1>")
            except:
                pass

    def _on_task_click(self, event, task: Task):
        """Обработка клика по задаче"""
        self.select_task(task)
        self.drag_data["task"] = task
        self.drag_data["start_x"] = event.x_root
        self.drag_data["start_y"] = event.y_root

    def _on_task_drag(self, event, task: Task, widget: tk.Widget):
        """Обработка перетаскивания задачи"""
        if not self.drag_data["widget"]:
            self.drag_data["widget"] = tk.Toplevel(self.task_manager.root)
            self.drag_data["widget"].overrideredirect(True)
            self.drag_data["widget"].attributes("-alpha", 0.8)
            
            drag_label = tk.Label(
                self.drag_data["widget"],
                text=task.title[:20] + "..." if len(task.title) > 20 else task.title,
                bg=get_priority_color(task.priority),
                fg='white',
                font=('Arial', 9, 'bold'),
                padx=10,
                pady=5
            )
            drag_label.pack()
        
        x = event.x_root - 20
        y = event.y_root - 10
        self.drag_data["widget"].geometry(f"+{x}+{y}")

    def _on_task_release(self, event):
        """Обработка отпускания задачи"""
        if self.drag_data["widget"]:
            self.drag_data["widget"].destroy()
            self.drag_data["widget"] = None

    def _on_quadrant_enter(self, event, quadrant: int):
        """Обработка входа в квадрант при перетаскивании"""
        if self.drag_data["task"] and self.drag_data["widget"]:
            self.quadrants[quadrant]['frame'].config(relief='groove', bd=4)

    def _on_quadrant_leave(self, event, quadrant: int):
        """Обработка выхода из квадранта при перетаскивании"""
        if self.drag_data["task"] and self.drag_data["widget"]:
            self.quadrants[quadrant]['frame'].config(relief='solid', bd=2)

    def _on_quadrant_drop(self, event, quadrant: int):
        """Обработка отпускания задачи в квадранте"""
        if self.drag_data["task"] and self.drag_data["task"].quadrant != quadrant:
            task = self.drag_data["task"]
            logger.info(f"Dropping task '{task.title}' into quadrant {quadrant}")
            
            self.task_manager.move_task_to_quadrant(task, quadrant)
            
            # Сбрасываем визуальные эффекты только если была подсветка
            if self.quadrants[quadrant]['frame']['relief'] == 'groove':
                self.quadrants[quadrant]['frame'].config(relief='solid', bd=2)
        
        # Очищаем данные перетаскивания
        self.drag_data["task"] = None
        if self.drag_data["widget"]:
            self.drag_data["widget"] = None

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def _show_context_menu(self, event, task: Task, current_quadrant: int):
        """Показать контекстное меню"""
        self.selected_task = task
        self.task_manager.select_task(task)
        
        # Создаем меню с учетом текущего квадранта
        self.setup_context_menu(current_quadrant)
        
        try:
            # Показываем меню
            self.context_menu.tk_popup(event.x_root, event.y_root)
            self.menu_visible = True
            
            # Ждем немного, чтобы меню появилось
            self.context_menu.update_idletasks()
            
            # Захватываем все события мыши для закрытия меню при клике вне его
            def close_on_click(e):
                # Получаем координаты меню
                try:
                    menu_x = self.context_menu.winfo_rootx()
                    menu_y = self.context_menu.winfo_rooty()
                    menu_width = self.context_menu.winfo_width()
                    menu_height = self.context_menu.winfo_height()
                    
                    # Проверяем, был ли клик вне меню
                    if not (menu_x <= e.x_root <= menu_x + menu_width and
                            menu_y <= e.y_root <= menu_y + menu_height):
                        self.hide_context_menu()
                except:
                    self.hide_context_menu()
            
            # Привязываем обработчик к окну
            self.task_manager.root.bind("<Button-1>", close_on_click, add="+")
            
        except Exception as e:
            logger.error(f"Error showing context menu: {e}")
            self.menu_visible = False
        
        # Предотвращаем распространение события
        return "break"
    
    def _on_menu_leave(self, event):
        """Обработчик для отслеживания выхода курсора из меню"""
        # Даем небольшую задержку, чтобы не закрывать меню слишком быстро
        self.context_menu.after(100, self._check_menu_focus)

    def toggle_task_completion(self, completed: bool):
        """Переключение статуса выполнения задачи"""
        if self.selected_task:
            self.task_manager.toggle_task_completion(self.selected_task, completed)
            self.hide_context_menu()

    def move_selected_to_quadrant(self, target_quadrant: int):
        """Перемещение выбранной задачи в другой квадрант"""
        if not self.selected_task:
            return

        logger.info(f"Moving selected task to quadrant {target_quadrant}")
        self.task_manager.move_task_to_quadrant(self.selected_task, target_quadrant)
        self.hide_context_menu()

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if not self.selected_task:
            return

        logger.info("Moving selected task to backlog")
        self.task_manager.move_task_to_backlog(self.selected_task)
        self.hide_context_menu()

    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        if self.selected_task:
            self.task_manager.current_task = self.selected_task
            self.task_manager.edit_current_task()
            self.hide_context_menu()

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if not self.selected_task:
            return

        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{self.selected_task.title}'?"):
            self.task_manager.task_service.delete_task(self.selected_task.id)
            self.hide_context_menu()

    def edit_start_time(self):
        """Редактирование времени начала дня"""
        current_time = self.time_labels[1]['text']
        new_time = simpledialog.askstring(
            "Редактирование времени",
            "Введите время начала дня (ЧЧ:ММ):",
            initialvalue=current_time
        )
        
        if new_time:
            try:
                time_parts = new_time.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                self.update_time_labels(hour, minute)
            except:
                messagebox.showerror("Ошибка", "Неверный формат времени! Используйте ЧЧ:ММ")

    def update_time_labels(self, start_hour: int, start_minute: int = 0):
        """Обновление времени квадрантов"""
        base_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        for quad_id in range(1, 5):
            quad_time = base_time + timedelta(hours=(quad_id - 1) * 3)
            
            if quad_id == 4:
                end_time = quad_time + timedelta(hours=3)
                time_str = f"{quad_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            else:
                time_str = quad_time.strftime('%H:%M')
            
            self.time_labels[quad_id].config(text=time_str)