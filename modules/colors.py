# -*- coding: utf-8 -*-
"""
Task Manager - Цвета и стили (Material Design)
"""


def get_priority_color(priority: int) -> str:
    """Вычисление цвета для приоритета (Material Design градиент)"""
    # Material Design цветовая схема от зеленого к красному
    colors = [
        "#4CAF50",  # 1 - Material Green 500
        "#66BB6A",  # 2 - Material Green 400
        "#81C784",  # 3 - Material Green 300
        "#A5D6A7",  # 4 - Material Green 200
        "#FFF176",  # 5 - Material Yellow 300
        "#FFD54F",  # 6 - Material Yellow 400
        "#FFB74D",  # 7 - Material Orange 300
        "#FF8A65",  # 8 - Material Deep Orange 300
        "#EF5350",  # 9 - Material Red 400
        "#F44336"   # 10 - Material Red 500
    ]
    
    # Обеспечиваем, что приоритет в диапазоне 1-10
    priority = max(1, min(10, priority))
    return colors[priority - 1]


def get_completed_color() -> str:
    """Цвет для выполненных задач"""
    return "#BDBDBD"  # Material Grey 400


def get_pastel_color(hue: int, saturation: float = 0.3, lightness: float = 0.9) -> str:
    """Генерация пастельного цвета по оттенку (Material Design Light)"""
    import colorsys

    # Конвертируем HSL в RGB
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, lightness, saturation)

    # Конвертируем в hex
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# Цвета квадрантов (Material Design пастельные)
QUADRANT_COLORS = {
    1: "#E8F5E9",  # Material Green 50
    2: "#E3F2FD",  # Material Blue 50
    3: "#FFF3E0",  # Material Orange 50
    4: "#F3E5F5",  # Material Purple 50
}

# Системные цвета интерфейса (Material Design)
UI_COLORS = {
    'primary': '#1976D2',      # Material Blue 700
    'accent': '#FF6F00',       # Material Amber 900
    'success': '#388E3C',      # Material Green 700
    'warning': '#F57C00',      # Material Orange 700
    'error': '#D32F2F',        # Material Red 700
    'background': '#FAFAFA',   # Material Grey 50
    'text_primary': '#212121', # Material Grey 900
    'text_secondary': '#757575', # Material Grey 600
    'border': '#E0E0E0',       # Material Grey 300
    'inactive': '#F5F5F5',     # Material Grey 100
    'disabled': '#9E9E9E',     # Material Grey 500
}