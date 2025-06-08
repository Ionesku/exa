# -*- coding: utf-8 -*-
"""
Task Manager - Цвета и стили
"""


def get_priority_color(priority: int) -> str:
    """Вычисление цвета для приоритета (градиент от зеленого к красному)"""
    # Нормализация приоритета к диапазону 0-1
    ratio = (priority - 1) / 9.0

    # Интерполяция между зеленым (0, 255, 0) и красным (255, 0, 0)
    red = int(255 * ratio)
    green = int(255 * (1 - ratio))
    blue = 0

    return f"#{red:02x}{green:02x}{blue:02x}"


def get_pastel_color(hue: int, saturation: float = 0.3, lightness: float = 0.8) -> str:
    """Генерация пастельного цвета по оттенку"""
    import colorsys

    # Конвертируем HSL в RGB
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, lightness, saturation)

    # Конвертируем в hex
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# Базовые цвета интерфейса
QUADRANT_COLORS = {
    1: get_pastel_color(120, 0.25, 0.9),  # Светло-зеленый
    2: get_pastel_color(210, 0.25, 0.9),  # Светло-голубой
    3: get_pastel_color(30, 0.25, 0.9),  # Светло-оранжевый
    4: get_pastel_color(270, 0.25, 0.9),  # Светло-фиолетовый
}

UI_COLORS = {
    'inactive': '#F8F8F8',
    'primary': '#2196F3',
    'accent': '#FF5722',
    'text': '#212121',
    'text_secondary': '#757575',
    'background': '#FFFFFF',
    'border': '#E0E0E0'
}