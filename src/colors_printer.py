# colors_printer.py
import random

colors = [
    '\033[92m',  # Green
    '\033[93m',  # Yellow
    '\033[96m',  # Cyan
    '\033[91m',  # Red
]

reset = '\033[0m'  # Reset to default color


def create_colorful_wall(width=50, height=4):
    """Create a colorful wall of hash symbols"""
    for row in range(height):
        line = ""
        for col in range(width):
            color = random.choice(colors)
            line += f"{color}#{reset}"
        print(line)


def colored_print(text, color_index):
    """Print text in a specific color using the colors array"""
    if 0 <= color_index < len(colors):
        print(f"{colors[color_index]}{text}{reset}")
    else:
        print(text)  # Print normally if index is invalid


def colored_print_info_type(indicator_text, color_index, regular_text):
    if 0 <= color_index < len(colors):
        print(f"{colors[color_index]}{indicator_text}{reset}{regular_text}")
    else:
        # Print normally if index is invalid
        print(indicator_text + " :: " + regular_text)


def wrap_text_in_color(text, color_index):
    return f"{colors[color_index]}{text}{reset}"
