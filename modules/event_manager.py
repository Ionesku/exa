# -*- coding: utf-8 -*-
"""
Task Manager - Менеджер событий (паттерн Observer)
"""

from typing import Dict, List, Callable, Any
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Типы событий в приложении"""
    # События задач
    TASK_CREATED = auto()
    TASK_UPDATED = auto()
    TASK_DELETED = auto()
    TASK_MOVED = auto()
    TASK_COMPLETED = auto()
    
    # События квадрантов
    QUADRANT_UPDATED = auto()
    
    # События дня
    DAY_STARTED = auto()
    DAY_ENDED = auto()
    DATE_CHANGED = auto()
    
    # События UI
    REFRESH_REQUIRED = auto()
    SELECTION_CHANGED = auto()


class Event:
    """Класс события"""
    def __init__(self, event_type: EventType, data: Any = None, source: Any = None):
        self.type = event_type
        self.data = data
        self.source = source
        
    def __repr__(self):
        return f"Event({self.type.name}, data={self.data})"


class EventManager:
    """Менеджер событий для координации компонентов"""
    
    def __init__(self):
        self._observers: Dict[EventType, List[Callable]] = {}
        self._event_queue: List[Event] = []
        self._processing = False
        
    def subscribe(self, event_type: EventType, callback: Callable):
        """Подписка на событие"""
        if event_type not in self._observers:
            self._observers[event_type] = []
        
        if callback not in self._observers[event_type]:
            self._observers[event_type].append(callback)
            logger.debug(f"Subscribed {callback.__name__} to {event_type.name}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Отписка от события"""
        if event_type in self._observers and callback in self._observers[event_type]:
            self._observers[event_type].remove(callback)
            logger.debug(f"Unsubscribed {callback.__name__} from {event_type.name}")
    
    def emit(self, event: Event):
        """Отправка события"""
        logger.info(f"Emitting event: {event}")
        
        # Добавляем в очередь для предотвращения рекурсии
        self._event_queue.append(event)
        
        # Если уже обрабатываем события, выходим
        if self._processing:
            return
        
        # Обрабатываем очередь событий
        self._process_event_queue()
    
    def _process_event_queue(self):
        """Обработка очереди событий"""
        self._processing = True
        
        try:
            while self._event_queue:
                event = self._event_queue.pop(0)
                
                if event.type in self._observers:
                    for callback in self._observers[event.type][:]:  # Копия для безопасности
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Error in callback {callback.__name__}: {e}")
        finally:
            self._processing = False
    
    def emit_now(self, event_type: EventType, data: Any = None, source: Any = None):
        """Быстрый метод для отправки события"""
        self.emit(Event(event_type, data, source))