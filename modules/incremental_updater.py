# -*- coding: utf-8 -*-
"""
Task Manager - Система инкрементальных обновлений
Создайте файл modules/incremental_updater.py
"""

import tkinter as tk
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import logging

from .task_models import Task
from .event_manager import EventType

logger = logging.getLogger(__name__)


@dataclass
class UpdateContext:
    """Контекст обновления"""
    added_tasks: Set[int] = None
    removed_tasks: Set[int] = None
    updated_tasks: Set[int] = None
    moved_tasks: Dict[int, Tuple[int, int]] = None  # task_id -> (from, to)
    
    def __post_init__(self):
        if self.added_tasks is None:
            self.added_tasks = set()
        if self.removed_tasks is None:
            self.removed_tasks = set()
        if self.updated_tasks is None:
            self.updated_tasks = set()
        if self.moved_tasks is None:
            self.moved_tasks = {}


class IncrementalUpdater:
    """Менеджер инкрементальных обновлений UI"""
    
    def __init__(self):
        self.task_cache: Dict[int, Task] = {}
        self.widget_cache: Dict[str, tk.Widget] = {}
        self.last_state: Dict[str, any] = {}
        
    def calculate_diff(self, old_tasks: List[Task], new_tasks: List[Task]) -> UpdateContext:
        """Вычисление разницы между старым и новым состоянием"""
        context = UpdateContext()
        
        old_dict = {t.id: t for t in old_tasks}
        new_dict = {t.id: t for t in new_tasks}
        
        # Найти добавленные задачи
        for task_id in new_dict:
            if task_id not in old_dict:
                context.added_tasks.add(task_id)
        
        # Найти удаленные задачи
        for task_id in old_dict:
            if task_id not in new_dict:
                context.removed_tasks.add(task_id)
        
        # Найти измененные задачи
        for task_id in new_dict:
            if task_id in old_dict:
                old_task = old_dict[task_id]
                new_task = new_dict[task_id]
                
                # Проверяем перемещение
                if old_task.quadrant != new_task.quadrant:
                    context.moved_tasks[task_id] = (old_task.quadrant, new_task.quadrant)
                
                # Проверяем другие изменения
                if (old_task.title != new_task.title or
                    old_task.is_completed != new_task.is_completed or
                    old_task.priority != new_task.priority or
                    old_task.importance != new_task.importance):
                    context.updated_tasks.add(task_id)
        
        return context
    
    def should_update_widget(self, widget_id: str, old_value: any, new_value: any) -> bool:
        """Определить, нужно ли обновлять виджет"""
        if widget_id not in self.last_state:
            self.last_state[widget_id] = old_value
            return True
        
        if self.last_state[widget_id] != new_value:
            self.last_state[widget_id] = new_value
            return True
            
        return False
    
    def animate_widget_change(self, widget: tk.Widget, property_name: str, 
                            from_value: any, to_value: any, duration: int = 200):
        """Анимация изменения свойства виджета"""
        steps = 10
        step_duration = duration // steps
        
        if property_name == 'bg' and isinstance(from_value, str) and isinstance(to_value, str):
            # Анимация цвета фона
            self._animate_color(widget, from_value, to_value, steps, step_duration)
        else:
            # Простое изменение
            widget.config(**{property_name: to_value})
    
    def _animate_color(self, widget: tk.Widget, from_color: str, to_color: str, 
                      steps: int, step_duration: int):
        """Анимация изменения цвета"""
        try:
            # Преобразуем цвета в RGB
            from_rgb = self._hex_to_rgb(from_color)
            to_rgb = self._hex_to_rgb(to_color)
            
            def update_color(step):
                if step >= steps:
                    widget.config(bg=to_color)
                    return
                
                # Интерполяция цвета
                ratio = step / steps
                r = int(from_rgb[0] + (to_rgb[0] - from_rgb[0]) * ratio)
                g = int(from_rgb[1] + (to_rgb[1] - from_rgb[1]) * ratio)
                b = int(from_rgb[2] + (to_rgb[2] - from_rgb[2]) * ratio)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                widget.config(bg=color)
                
                # Следующий шаг
                widget.after(step_duration, lambda: update_color(step + 1))
            
            update_color(0)
            
        except Exception as e:
            # Если анимация не удалась, просто установим цвет
            widget.config(bg=to_color)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Преобразование hex в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def fade_out_widget(self, widget: tk.Widget, callback: callable = None):
        """Плавное исчезновение виджета"""
        def fade_step(alpha):
            if alpha <= 0:
                widget.destroy()
                if callback:
                    callback()
                return
            
            # Уменьшаем прозрачность (эмуляция через изменение цвета)
            widget.after(20, lambda: fade_step(alpha - 0.1))
        
        fade_step(1.0)
    
    def fade_in_widget(self, widget: tk.Widget):
        """Плавное появление виджета"""
        # Простая реализация - виджет сразу видим
        # В будущем можно добавить более сложную анимацию
        pass


class SmartUpdateMixin:
    """Миксин для умного обновления виджетов"""
    
    def __init__(self):
        self._widget_states = {}
        self._update_queue = []
        self._updating = False
        
    def queue_update(self, update_func, *args, **kwargs):
        """Добавить обновление в очередь"""
        self._update_queue.append((update_func, args, kwargs))
        
        if not self._updating:
            self._process_update_queue()
    
    def _process_update_queue(self):
        """Обработка очереди обновлений"""
        if not self._update_queue:
            self._updating = False
            return
        
        self._updating = True
        
        # Обработка пакета обновлений
        batch_size = min(5, len(self._update_queue))
        for _ in range(batch_size):
            if self._update_queue:
                func, args, kwargs = self._update_queue.pop(0)
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in update queue: {e}")
        
        # Планируем следующий пакет
        if hasattr(self, 'after'):
            self.after(10, self._process_update_queue)
        else:
            self._process_update_queue()
    
    def get_widget_state(self, widget_id: str) -> any:
        """Получить сохраненное состояние виджета"""
        return self._widget_states.get(widget_id)
    
    def set_widget_state(self, widget_id: str, state: any):
        """Сохранить состояние виджета"""
        self._widget_states[widget_id] = state
    
    def has_widget_changed(self, widget_id: str, new_state: any) -> bool:
        """Проверить, изменилось ли состояние виджета"""
        old_state = self.get_widget_state(widget_id)
        if old_state != new_state:
            self.set_widget_state(widget_id, new_state)
            return True
        return False