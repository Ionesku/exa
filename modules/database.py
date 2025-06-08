# -*- coding: utf-8 -*-
"""
Task Manager - Менеджер базы данных
"""

import sqlite3
from typing import List
from modules.task_models import Task, TaskType


class DatabaseManager:
    """Менеджер базы данных"""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица типов задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#2196F3',
                description TEXT DEFAULT ''
            )
        ''')

        # Таблица задач с добавлением has_duration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                importance INTEGER DEFAULT 1,
                duration INTEGER DEFAULT 30,
                has_duration BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 5,
                task_type_id INTEGER DEFAULT 1,
                is_completed BOOLEAN DEFAULT FALSE,
                quadrant INTEGER DEFAULT 0,
                date_created TEXT NOT NULL,
                date_scheduled TEXT DEFAULT '',
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern TEXT DEFAULT '',
                move_count INTEGER DEFAULT 0,
                FOREIGN KEY (task_type_id) REFERENCES task_types (id)
            )
        ''')

        # Добавляем колонку has_duration если её нет
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN has_duration BOOLEAN DEFAULT FALSE')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Колонка уже существует

        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Добавляем базовые типы задач если их нет
        cursor.execute('SELECT COUNT(*) FROM task_types')
        if cursor.fetchone()[0] == 0:
            default_types = [
                ('Работа', '#FF5722', 'Рабочие задачи'),
                ('Дом', '#4CAF50', 'Домашние дела'),
                ('Интерес', '#9C27B0', 'Личные интересы'),
                ('Цель', '#FF9800', 'Долгосрочные цели')
            ]
            cursor.executemany(
                'INSERT INTO task_types (name, color, description) VALUES (?, ?, ?)',
                default_types
            )

        conn.commit()
        conn.close()

    def get_tasks(self, date: str = None, include_backlog: bool = False) -> List[Task]:
        """Получить задачи за определенную дату"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date and not include_backlog:
            # Только задачи для конкретной даты
            cursor.execute('SELECT * FROM tasks WHERE date_scheduled = ?', (date,))
        elif include_backlog and not date:
            # Только задачи из бэклога (без даты)
            cursor.execute('SELECT * FROM tasks WHERE date_scheduled = "" OR date_scheduled IS NULL')
        elif date and include_backlog:
            # Задачи для даты + бэклог
            cursor.execute(
                'SELECT * FROM tasks WHERE date_scheduled = ? OR date_scheduled = "" OR date_scheduled IS NULL',
                (date,)
            )
        else:
            # Все задачи
            cursor.execute('SELECT * FROM tasks')

        rows = cursor.fetchall()
        conn.close()

        tasks = []
        for row in rows:
            # Проверяем наличие поля has_duration
            if len(row) >= 15:  # Новая структура с has_duration
                task = Task(
                    id=row[0], title=row[1], content=row[2], importance=row[3],
                    duration=row[4], has_duration=bool(row[5]), priority=row[6],
                    task_type_id=row[7], is_completed=bool(row[8]), quadrant=row[9],
                    date_created=row[10], date_scheduled=row[11], is_recurring=bool(row[12]),
                    recurrence_pattern=row[13], move_count=row[14]
                )
            else:  # Старая структура без has_duration
                task = Task(
                    id=row[0], title=row[1], content=row[2], importance=row[3],
                    duration=row[4], has_duration=False, priority=row[5],
                    task_type_id=row[6], is_completed=bool(row[7]), quadrant=row[8],
                    date_created=row[9], date_scheduled=row[10], is_recurring=bool(row[11]),
                    recurrence_pattern=row[12], move_count=row[13]
                )
            tasks.append(task)

        return tasks

    def save_task(self, task: Task) -> int:
        """Сохранить задачу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if task.id == 0:  # Новая задача
            cursor.execute('''
                INSERT INTO tasks (title, content, importance, duration, has_duration, priority,
                                 task_type_id, is_completed, quadrant, date_created,
                                 date_scheduled, is_recurring, recurrence_pattern, move_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task.title, task.content, task.importance, task.duration,
                  task.has_duration, task.priority, task.task_type_id, task.is_completed,
                  task.quadrant, task.date_created, task.date_scheduled,
                  task.is_recurring, task.recurrence_pattern, task.move_count))
            task_id = cursor.lastrowid
        else:  # Обновление
            cursor.execute('''
                UPDATE tasks SET title=?, content=?, importance=?, duration=?, has_duration=?,
                               priority=?, task_type_id=?, is_completed=?,
                               quadrant=?, date_scheduled=?, is_recurring=?,
                               recurrence_pattern=?, move_count=?
                WHERE id=?
            ''', (task.title, task.content, task.importance, task.duration,
                  task.has_duration, task.priority, task.task_type_id, task.is_completed,
                  task.quadrant, task.date_scheduled, task.is_recurring,
                  task.recurrence_pattern, task.move_count, task.id))
            task_id = task.id

        conn.commit()
        conn.close()
        return task_id

    def delete_task(self, task_id: int):
        """Удалить задачу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
        conn.close()

    def get_task_types(self) -> List[TaskType]:
        """Получить типы задач"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM task_types')
        rows = cursor.fetchall()
        conn.close()

        return [TaskType(id=row[0], name=row[1], color=row[2], description=row[3])
                for row in rows]

    def save_task_type(self, task_type: TaskType) -> int:
        """Сохранить тип задачи"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if task_type.id == 0:  # Новый тип
            cursor.execute(
                'INSERT INTO task_types (name, color, description) VALUES (?, ?, ?)',
                (task_type.name, task_type.color, task_type.description)
            )
            type_id = cursor.lastrowid
        else:  # Обновление
            cursor.execute(
                'UPDATE task_types SET name=?, color=?, description=? WHERE id=?',
                (task_type.name, task_type.color, task_type.description, task_type.id)
            )
            type_id = task_type.id

        conn.commit()
        conn.close()
        return type_id

    def save_setting(self, key: str, value: str):
        """Сохранить настройку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str = "") -> str:
        """Получить настройку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default