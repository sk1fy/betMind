"""Color and style constants for TUI."""

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"

# Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright colors
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background
BG_BLUE = "\033[44m"
BG_GREEN = "\033[42m"
BG_RED = "\033[41m"
BG_YELLOW = "\033[43m"

# Box drawing
BOX_H = "─"
BOX_V = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_T = "┬"
BOX_B = "┴"
BOX_L = "├"
BOX_R = "┤"
BOX_X = "┼"

# Double box
DBOX_H = "═"
DBOX_V = "║"
DBOX_TL = "╔"
DBOX_TR = "╗"
DBOX_BL = "╚"
DBOX_BR = "╝"

# Symbols
ARROW_RIGHT = "►"
ARROW_LEFT = "◄"
CHECK = "✓"
CROSS = "✗"
BULLET = "●"
CIRCLE = "○"
STAR = "★"
BAR_FULL = "█"
BAR_HALF = "▌"
BAR_EMPTY = "░"


def colored(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def header_box(title: str, width: int = 56) -> str:
    """Create a double-line header box."""
    padding = width - len(title) - 4
    left_pad = padding // 2
    right_pad = padding - left_pad
    lines = [
        f"{BRIGHT_CYAN}{DBOX_TL}{DBOX_H * (width - 2)}{DBOX_TR}{RESET}",
        f"{BRIGHT_CYAN}{DBOX_V}{RESET}{' ' * left_pad}  {BOLD}{BRIGHT_WHITE}{title}{RESET}  {' ' * right_pad}{BRIGHT_CYAN}{DBOX_V}{RESET}",
        f"{BRIGHT_CYAN}{DBOX_BL}{DBOX_H * (width - 2)}{DBOX_BR}{RESET}",
    ]
    return "\n".join(lines)


def section_line(width: int = 56) -> str:
    return f"{DIM}{BOX_H * width}{RESET}"


def progress_bar(value: float, width: int = 30, color: str = GREEN) -> str:
    """Create a progress bar. value should be 0.0-1.0."""
    filled = int(value * width)
    empty = width - filled
    return f"{color}{BAR_FULL * filled}{DIM}{BAR_EMPTY * empty}{RESET}"


def probability_bar(prob: float, label1: str = "", label2: str = "", width: int = 40) -> str:
    """Create a dual probability bar."""
    t1_width = int(prob * width)
    t2_width = width - t1_width
    bar = (
        f"{GREEN}{BAR_FULL * t1_width}{RESET}"
        f"{RED}{BAR_FULL * t2_width}{RESET}"
    )
    return f"  {label1} {bar} {label2}\n  {GREEN}{prob:.1%}{RESET}{' ' * (width - 8)}{RED}{1 - prob:.1%}{RESET}"
