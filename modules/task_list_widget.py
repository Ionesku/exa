# -*- coding: utf-8 -*-
"""
Task Manager - Виджет списка задач с инкрементальными обновлениями
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional, Set
import logging

from .task_models import Task
from .colors import get_priority_color, get_completed_color
from .incremental_updater import IncrementalUpdater, SmartUpdateMixin

logger = logging.getLogger(__name__)


class TaskListWidget(SmartUpdateMixin):
    """Виджет списка задач с оптимизированными обновлениями"""

    def __init__(self, parent, task_manager):
        super().__init__()
        self.parent = parent
        self.task_manager = task_manager
        self.selected_task: Optional[Task] = None
        self.task_groups = {}  # Хранение групп задач
        self.group_widgets = {}  # Виджеты групп
        self.group_states = {}  # Состояния групп (свернута/развернута)
        self.drag_data = {"task": None, "widget": None}
        self.updater = IncrementalUpdater()
        
        # Кеш для отслеживания состояния
        self._task_widgets_cache = {}  # task_id -> widget
        self._current_tasks = {
            'active': {},  # type_name -> set of task_ids
            'completed': {}  # type_name -> set of task_ids
        }
        
        self.setup_task_list()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.task_manager.root, tearoff=0)
        
        self.context_menu.add_command(label="В первый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(1))
        self.context_menu.add_command(label="Во второй квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(2))
        self.context_menu.add_command(label="В третий квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(3))
        self.context_menu.add_command(label="В четвертый квадрант", 
                                     command=lambda: self.move_selected_to_quadrant(4))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="В бэклог", 
                                     command=self.move_selected_to_backlog)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_task)

    def setup_task_list(self):
        """Создание списка задач"""
        self.main_frame = ttk.LabelFrame(self.parent, text="Задачи")
        
        self.main_frame.configure(width=280)
        self.main_frame.pack_propagate(False)

        ttk.Button(self.main_frame, text="+ Новая задача",
                   command=self.task_manager.create_new_task_dialog).pack(
            fill='x', padx=5, pady=(5, 0))

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка "Активные"
        self.active_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.active_frame, text="Активные (0)")
        self.setup_task_tab(self.active_frame, "active")

        # Вкладка "Выполненные"
        self.completed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.completed_frame, text="Выполненные (0)")
        self.setup_task_tab(self.completed_frame, "completed")

    def setup_task_tab(self, parent, tab_type):
        """Настройка вкладки с задачами"""
        self._create_scrollable_area(parent, tab_type)

    def _create_scrollable_area(self, parent, tab_type):
        """Создание прокручиваемой области"""
        canvas = tk.Canvas(parent, bg='white', width=260)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(scrollable_window, width=e.width)
        )
        
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Добавляем пустой заполнитель
        empty_label = tk.Label(scrollable_frame, text="Нет задач", 
                              bg='white', fg='gray', font=('Arial', 10))
        
        if tab_type == "active":
            self.active_canvas = canvas
            self.active_scrollable_frame = scrollable_frame
            self.active_empty_label = empty_label
        else:
            self.completed_canvas = canvas
            self.completed_scrollable_frame = scrollable_frame
            self.completed_empty_label = empty_label

    def update_tasks(self, tasks: List[Task]):
        """Инкрементальное обновление списка задач"""
        logger.debug("Starting incremental task list update")
        
        # Получаем типы задач
        task_types = self.task_manager.get_task_types()
        type_map = {t.id: t for t in task_types}
        
        # Разделяем задачи
        active_tasks = [t for t in tasks if not t.is_completed and t.quadrant == 0]
        completed_tasks = [t for t in tasks if t.is_completed]
        
        # Группируем по типам
        active_groups = self._group_tasks_by_type(active_tasks, type_map)
        completed_groups = self._group_tasks_by_type(completed_tasks, type_map)
        
        # Обновляем вкладки инкрементально
        self._update_tab_incremental(self.active_scrollable_frame, active_groups, "active", self.active_empty_label)
        self._update_tab_incremental(self.completed_scrollable_frame, completed_groups, "completed", self.completed_empty_label)
        
        # Обновляем заголовки только если изменилось количество
        active_count = len(active_tasks)
        completed_count = len(completed_tasks)
        
        current_active_text = self.notebook.tab(0, "text")
        current_completed_text = self.notebook.tab(1, "text")
        
        new_active_text = f"Активные ({active_count})"
        new_completed_text = f"Выполненные ({completed_count})"
        
        if current_active_text != new_active_text:
            self.notebook.tab(0, text=new_active_text)
        if current_completed_text != new_completed_text:
            self.notebook.tab(1, text=new_completed_text)
    
    def _group_tasks_by_type(self, tasks: List[Task], type_map: Dict[int, any]) -> Dict[str, List[Task]]:
        """Группировка задач по типам"""
        groups = {}
        
        for task in tasks:
            task_type = type_map.get(task.task_type_id)
            type_name = task_type.name if task_type else "Без типа"
            
            if type_name not in groups:
                groups[type_name] = []
            groups[type_name].append(task)
        
        return groups
    
    def _update_tab_incremental(self, parent_frame, groups: Dict[str, List[Task]], tab_type: str, empty_label):
        """Инкрементальное обновление вкладки"""
        group_key = f"{tab_type}_groups"
        if group_key not in self.group_widgets:
            self.group_widgets[group_key] = {}
        
        current_groups = self._current_tasks[tab_type]
        new_groups = {type_name: {t.id for t in tasks} for type_name, tasks in groups.items()}
        
        # Определяем изменения на уровне групп
        all_type_names = set(current_groups.keys()) | set(new_groups.keys())
        
        # Если нет задач
        if not groups:
            # Скрываем все группы
            for widget_data in self.group_widgets[group_key].values():
                if widget_data['frame'].winfo_exists():
                    widget_data['frame'].pack_forget()
            
            # Показываем пустой заполнитель
            if not empty_label.winfo_manager():
                empty_label.pack(expand=True, pady=20)
            
            self._current_tasks[tab_type] = {}
            return
        
        # Скрываем пустой заполнитель
        if empty_label.winfo_manager():
            empty_label.pack_forget()
        
        # Обновляем группы
        for type_name in sorted(all_type_names):
            if type_name not in new_groups:
                # Группа удалена
                if type_name in self.group_widgets[group_key]:
                    self.group_widgets[group_key][type_name]['frame'].pack_forget()
            else:
                # Группа существует или новая
                new_tasks = groups.get(type_name, [])
                current_task_ids = current_groups.get(type_name, set())
                new_task_ids = new_groups[type_name]
                
                if type_name not in self.group_widgets[group_key]:
                    # Создаем новую группу
                    self._create_group_widget(parent_frame, type_name, new_tasks, tab_type)
                else:
                    # Обновляем существующую группу
                    self._update_group_incremental(type_name, new_tasks, current_task_ids, new_task_ids, tab_type)
        
        # Обновляем кеш
        self._current_tasks[tab_type] = new_groups
    
    def _update_group_incremental(self, type_name: str, tasks: List[Task], 
                                 current_ids: Set[int], new_ids: Set[int], tab_type: str):
        """Инкрементальное обновление группы"""
        group_key = f"{tab_type}_groups"
        group_data = self.group_widgets[group_key][type_name]
        
        # Обновляем заголовок группы если изменилось количество
        header_label = group_data.get('header_label')
        if header_label and header_label.winfo_exists():
            new_text = f"{type_name} ({len(tasks)})"
            if header_label['text'] != new_text:
                header_label.config(text=new_text)
        
        # Определяем изменения
        added_ids = new_ids - current_ids
        removed_ids = current_ids - new_ids
        common_ids = current_ids & new_ids
        
        container = group_data['container']
        
        # Удаляем виджеты удаленных задач
        for task_id in removed_ids:
            if task_id in self._task_widgets_cache:
                widget = self._task_widgets_cache[task_id]
                if widget.winfo_exists():
                    widget.destroy()
                del self._task_widgets_cache[task_id]
        
        # Обновляем существующие задачи
        for task in tasks:
            if task.id in common_ids and task.id in self._task_widgets_cache:
                widget = self._task_widgets_cache[task.id]
                if widget.winfo_exists() and self._task_changed(task, widget):
                    self._update_task_widget_properties(widget, task)
        
        # Добавляем новые задачи
        for task in tasks:
            if task.id in added_ids:
                self._create_task_widget(container, task)
        
        # Обеспечиваем видимость группы
        if not group_data['frame'].winfo_manager():
            group_data['frame'].pack(fill='x', pady=(0, 5))
    
    def _task_changed(self, task: Task, widget: tk.Widget) -> bool:
        """Проверка, изменилась ли задача"""
        if not hasattr(widget, '_task_state'):
            return True
        
        old_state = widget._task_state
        new_state = (task.title, task.is_completed, task.priority, task.importance, task.has_duration, task.duration)
        
        return old_state != new_state
    
    def _update_task_widget_properties(self, widget: tk.Widget, task: Task):
        """Обновление свойств виджета задачи"""
        # Обновляем цвет
        new_color = get_completed_color() if task.is_completed else get_priority_color(task.priority)
        current_color = widget.cget('bg')
        
        if current_color != new_color:
            widget.config(bg=new_color)
            # Обновляем дочерние виджеты
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
                        title = task.title
                        if len(title) > 25:
                            title = title[:22] + "..."
                        if task.is_completed:
                            title = f"✓ {title}"
                        subchild.config(text=title)
                    elif isinstance(subchild, tk.Label) and hasattr(subchild, '_is_info'):
                        info_parts = []
                        info_parts.append(f"В:{task.importance}")
                        info_parts.append(f"С:{task.priority}")
                        if task.has_duration:
                            info_parts.append(f"Д:{task.duration}м")
                        info_text = " | ".join(info_parts)
                        subchild.config(text=info_text)
        
        # Сохраняем новое состояние
        widget._task_state = (task.title, task.is_completed, task.priority, task.importance, task.has_duration, task.duration)
    
    def _create_group_widget(self, parent_frame, type_name: str, tasks: List[Task], tab_type: str):
        """Создание виджета группы задач"""
        group_frame = tk.Frame(parent_frame, bg='white')
        group_frame.pack(fill='x', pady=(0, 5))
        
        header_frame = tk.Frame(group_frame, bg='#E0E0E0', relief='solid', bd=1)
        header_frame.pack(fill='x')
        
        state_key = f"{tab_type}_{type_name}"
        if state_key not in self.group_states:
            self.group_states[state_key] = True
        
        is_expanded = self.group_states[state_key]
        toggle_text = "▼" if is_expanded else "▶"
        
        toggle_btn = tk.Label(header_frame, text=toggle_text, 
                             bg='#E0E0E0', font=('Arial', 10),
                             cursor='hand2')
        toggle_btn.pack(side='left', padx=(5, 0))
        
        group_label = tk.Label(header_frame, 
                              text=f"{type_name} ({len(tasks)})",
                              bg='#E0E0E0', font=('Arial', 10, 'bold'))
        group_label.pack(side='left', padx=5)
        
        tasks_container = tk.Frame(group_frame, bg='white')
        if is_expanded:
            tasks_container.pack(fill='x', padx=(20, 0))
        
        # Сохраняем данные группы
        group_key = f"{tab_type}_groups"
        self.group_widgets[group_key][type_name] = {
            'frame': group_frame,
            'container': tasks_container,
            'toggle_btn': toggle_btn,
            'header_label': group_label,
            'expanded': is_expanded
        }
        
        # Добавляем задачи
        for task in tasks:
            self._create_task_widget(tasks_container, task)
        
        # Обработчик сворачивания/разворачивания
        def toggle_group(e):
            self.group_states[state_key] = not self.group_states[state_key]
            self._update_group_visibility(state_key, tasks_container, toggle_btn)
        
        toggle_btn.bind('<Button-1>', toggle_group)
        group_label.bind('<Button-1>', toggle_group)
    
    def _update_group_visibility(self, state_key: str, container, toggle_widget):
        """Обновление видимости группы"""
        is_expanded = self.group_states[state_key]
        
        if is_expanded:
            container.pack(fill='x', padx=(20, 0))
            toggle_widget.config(text="▼")
        else:
            container.pack_forget()
            toggle_widget.config(text="▶")
    
    def _create_task_widget(self, parent_frame, task: Task):
        """Создание виджета задачи"""
        bg_color = get_completed_color() if task.is_completed else get_priority_color(task.priority)

        task_frame = tk.Frame(parent_frame,
                             bg=bg_color,
                             relief='solid', bd=1,
                             cursor='hand2')
        task_frame.pack(fill='x', pady=2)

        main_info_frame = tk.Frame(task_frame, bg=bg_color)
        main_info_frame.pack(fill='x', padx=5, pady=(3, 0))

        if task.is_planned:
            plan_label = tk.Label(main_info_frame, text="📅",
                                 bg=bg_color,
                                 font=('Arial', 8))
            plan_label.pack(side='right', padx=2)

        title = task.title
        if len(title) > 25:
            title = title[:22] + "..."
        
        if task.is_completed:
            title = f"✓ {title}"

        title_label = tk.Label(main_info_frame, text=title,
                              bg=bg_color,
                              fg='white', font=('Arial', 9, 'bold'),
                              anchor='w')
        title_label._is_title = True  # Маркер
        title_label.pack(fill='x')

        info_frame = tk.Frame(task_frame, bg=bg_color)
        info_frame.pack(fill='x', padx=5, pady=(0, 3))

        info_parts = []
        info_parts.append(f"В:{task.importance}")
        info_parts.append(f"С:{task.priority}")
        if task.has_duration:
            info_parts.append(f"Д:{task.duration}м")
        
        info_text = " | ".join(info_parts)
        
        info_label = tk.Label(info_frame, text=info_text,
                             bg=bg_color,
                             fg='white', font=('Arial', 8),
                             anchor='w')
        info_label._is_info = True  # Маркер
        info_label.pack(fill='x')

        # События
        for widget in [task_frame, main_info_frame, title_label, info_frame, info_label]:
            widget.bind("<Button-1>", lambda e, t=task: self._on_task_click(e, t))
            widget.bind("<B1-Motion>", lambda e, t=task, w=task_frame: self._on_task_drag(e, t, w))
            widget.bind("<ButtonRelease-1>", lambda e: self._on_task_release(e))
            widget.bind("<Button-3>", lambda e, t=task: self._show_context_menu(e, t))
        
        # Сохраняем в кеш
        self._task_widgets_cache[task.id] = task_frame
        task_frame._task_state = (task.title, task.is_completed, task.priority, task.importance, task.has_duration, task.duration)

    def _on_task_click(self, event, task: Task):
        """Обработка клика по задаче"""
        self.select_task(task)
        self.drag_data["task"] = task
        self.drag_data["start_x"] = event.x_root
        self.drag_data["start_y"] = event.y_root

    def _on_task_drag(self, event, task: Task, widget: tk.Widget):
        """Обработка перетаскивания"""
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
        
        self.drag_data["task"] = None

    def select_task(self, task: Task):
        """Выбор задачи"""
        self.selected_task = task
        self.task_manager.select_task(task)

    def _show_context_menu(self, event, task: Task):
        """Показать контекстное меню"""
        self.selected_task = task
        self.task_manager.select_task(task)
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def move_selected_to_quadrant(self, quadrant: int):
        """Перемещение выбранной задачи в квадрант"""
        if self.selected_task:
            logger.info(f"Moving task to quadrant {quadrant}")
            self.task_manager.move_task_to_quadrant(self.selected_task, quadrant)

    def move_selected_to_backlog(self):
        """Перемещение выбранной задачи в бэклог"""
        if self.selected_task:
            logger.info("Moving task to backlog")
            self.task_manager.move_task_to_backlog(self.selected_task)

    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        if self.selected_task:
            self.task_manager.current_task = self.selected_task
            self.task_manager.edit_current_task()

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if not self.selected_task:
            return

        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{self.selected_task.title}'?"):
            self.task_manager.task_service.delete_task(self.selected_task.id)