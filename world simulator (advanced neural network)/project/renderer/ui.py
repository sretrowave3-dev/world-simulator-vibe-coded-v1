"""
project/renderer/ui.py

Graphical User Interface control buttons and configuration panels using Pygame.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple, Callable, Optional
import pygame
_TEXT_SURFACE_CACHE: Dict[Tuple[int, str, int, int, int], pygame.Surface] = {}
_MAX_TEXT_CACHE_SIZE = 1024
_DEFAULT_FALLBACK_FONT: Optional[pygame.font.Font] = None
_CIRCLE_SPRITE_CACHE: Dict[Tuple[Tuple[int, int, int], int], pygame.Surface] = {}
_AURA_SPRITE_CACHE: Dict[Tuple[Tuple[int, int, int, int], int], pygame.Surface] = {}


def get_cached_circle_sprite(color: Tuple[int, int, int], radius: int) -> pygame.Surface:
    """Pre-renders and caches anti-aliased solid circle sprites for fast blitting."""
    key = (color, radius)
    surf = _CIRCLE_SPRITE_CACHE.get(key)
    if surf is not None:
        return surf
    if len(_CIRCLE_SPRITE_CACHE) >= 512:
        _CIRCLE_SPRITE_CACHE.clear()
    diam = max(2, radius * 2)
    surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (radius, radius), radius)
    _CIRCLE_SPRITE_CACHE[key] = surf
    return surf


def get_cached_aura_sprite(color_rgba: Tuple[int, int, int, int], radius: int) -> pygame.Surface:
    """Pre-renders and caches semi-transparent circular aura sprites."""
    key = (color_rgba, radius)
    surf = _AURA_SPRITE_CACHE.get(key)
    if surf is not None:
        return surf
    if len(_AURA_SPRITE_CACHE) >= 512:
        _AURA_SPRITE_CACHE.clear()
    diam = max(2, radius * 2)
    surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
    pygame.draw.circle(surf, color_rgba, (radius, radius), radius)
    _AURA_SPRITE_CACHE[key] = surf
    return surf


def get_cached_text(font: Optional[pygame.font.Font], text: str, color: Tuple[int, int, int]) -> pygame.Surface:
    """Hyper-fast text rendering using bounded dictionary cache to prevent re-rendering static strings every frame."""
    global _DEFAULT_FALLBACK_FONT
    if font is None:
        if _DEFAULT_FALLBACK_FONT is None:
            if not pygame.font.get_init():
                pygame.font.init()
            _DEFAULT_FALLBACK_FONT = pygame.font.SysFont("Segoe UI", 12)
        font = _DEFAULT_FALLBACK_FONT

    key = (id(font), text, color[0], color[1], color[2])
    surf = _TEXT_SURFACE_CACHE.get(key)
    if surf is not None:
        return surf
    if len(_TEXT_SURFACE_CACHE) >= _MAX_TEXT_CACHE_SIZE:
        _TEXT_SURFACE_CACHE.clear()
    surf = font.render(text, True, color)
    _TEXT_SURFACE_CACHE[key] = surf
    return surf


class Button:
    """Standard UI click button."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, callback: Callable[[], None]) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.is_hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        bg_color = (70, 70, 90) if self.is_hovered else (50, 50, 70)
        border_color = (150, 150, 200) if self.is_hovered else (100, 100, 150)

        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        txt_surface = get_cached_text(font, self.text, (255, 255, 255))
        tx = self.rect.x + (self.rect.width - txt_surface.get_width()) // 2
        ty = self.rect.y + (self.rect.height - txt_surface.get_height()) // 2
        surface.blit(txt_surface, (tx, ty))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class Checkbox:
    """Toggle switch checkbox."""

    def __init__(self, x: int, y: int, label: str, default_state: bool = False) -> None:
        self.rect = pygame.Rect(x, y, 18, 18)
        self.label = label
        self.checked = default_state
        # Extended hit rect to encompass the label (assume approx 120 pixels wide for text)
        self.hit_rect = pygame.Rect(x, y, 150, 20)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Hover effect
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.hit_rect.collidepoint(mouse_pos)
        
        box_color = (60, 60, 75) if hovered else (40, 40, 50)
        border_color = (180, 180, 220) if hovered else (150, 150, 180)

        pygame.draw.rect(surface, box_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)

        if self.checked:
            # Draw an inner check square
            inner_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, 12, 12)
            pygame.draw.rect(surface, (0, 255, 255), inner_rect)

        text_color = (255, 255, 255) if hovered else (200, 200, 200)
        lbl_surface = get_cached_text(font, self.label, text_color)
        surface.blit(lbl_surface, (self.rect.x + 25, self.rect.y + (self.rect.height - lbl_surface.get_height()) // 2))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hit_rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        return False


class Slider:
    """Horizontal draggable slider."""

    def __init__(self, x: int, y: int, width: int, min_val: float, max_val: float, default: float, label: str) -> None:
        self.rect = pygame.Rect(x, y, width, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default
        self.label = label
        self.is_dragging = False
        self.knob_radius = 8

    def _get_knob_x(self) -> int:
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val) if self.max_val > self.min_val else 0.0
        return self.rect.x + int(ratio * self.rect.width)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Draw label
        val_str = f"{self.value:.1f}" if isinstance(self.value, float) else str(self.value)
        lbl_surf = get_cached_text(font, f"{self.label}: {val_str}", (200, 200, 200))
        surface.blit(lbl_surf, (self.rect.x, self.rect.y - 20))

        # Draw track
        pygame.draw.rect(surface, (60, 60, 80), self.rect, border_radius=5)
        
        # Draw filled portion
        knob_x = self._get_knob_x()
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, knob_x - self.rect.x, self.rect.height)
        pygame.draw.rect(surface, (0, 200, 255), filled_rect, border_radius=5)

        # Draw knob
        knob_color = (255, 255, 255) if self.is_dragging else (200, 200, 220)
        pygame.draw.circle(surface, knob_color, (knob_x, self.rect.y + self.rect.height // 2), self.knob_radius)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_x = self._get_knob_x()
            knob_rect = pygame.Rect(knob_x - self.knob_radius, self.rect.y - 5, self.knob_radius * 2, self.rect.height + 10)
            if knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._update_value(event.pos[0])
                return True
        return False

    def _update_value(self, mouse_x: int) -> None:
        rel_x = max(0, min(mouse_x - self.rect.x, self.rect.width))
        ratio = rel_x / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)


class Selector:
    """Simple dropdown selector."""

    def __init__(self, x: int, y: int, width: int, options: List[str], label: str) -> None:
        self.rect = pygame.Rect(x, y, width, 25)
        self.options = options
        self.selected_idx = 0
        self.label = label
        self.is_open = False
        self.hovered_idx = -1

    @property
    def value(self) -> str:
        return self.options[self.selected_idx]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Draw label
        lbl_surf = get_cached_text(font, self.label, (200, 200, 200))
        surface.blit(lbl_surf, (self.rect.x, self.rect.y - 20))

        # Draw main box
        pygame.draw.rect(surface, (50, 50, 70), self.rect)
        pygame.draw.rect(surface, (150, 150, 200), self.rect, 1)

        val_surf = get_cached_text(font, self.value, (255, 255, 255))
        surface.blit(val_surf, (self.rect.x + 5, self.rect.y + 4))

        # Draw dropdown options if open
        if self.is_open:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * 25, self.rect.width, 25)
                bg_color = (80, 80, 100) if i == self.hovered_idx else (40, 40, 50)
                pygame.draw.rect(surface, bg_color, opt_rect)
                pygame.draw.rect(surface, (100, 100, 150), opt_rect, 1)
                
                opt_surf = get_cached_text(font, opt, (255, 255, 255))
                surface.blit(opt_surf, (opt_rect.x + 5, opt_rect.y + 4))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            if self.is_open:
                mouse_pos = event.pos
                self.hovered_idx = -1
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * 25, self.rect.width, 25)
                    if opt_rect.collidepoint(mouse_pos):
                        self.hovered_idx = i
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            elif self.is_open:
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * 25, self.rect.width, 25)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return True
                self.is_open = False  # Clicked outside
        return False


class Console:
    """Semi-transparent interactive developer/command overlay console."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.active = False
        self.input_text = ""
        self.history: List[str] = [
            "World Simulator Command Console",
            "Type 'help' to see available commands.",
            "Press ~ or Tab to close."
        ]
        self.command_history: List[str] = []
        self.history_index = -1
        self.max_history_lines = 15

    def toggle(self) -> None:
        self.active = not self.active
        self.input_text = ""

    def log(self, message: str) -> None:
        self.history.append(message)
        if len(self.history) > self.max_history_lines:
            self.history.pop(0)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.active:
            return

        # Draw semi-transparent dark backing
        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 230))  # Slate background with opacity
        surface.blit(overlay, (self.rect.x, self.rect.y))

        # Border
        pygame.draw.rect(surface, (0, 255, 200), self.rect, 1)

        # Draw console log history
        line_height = 20
        start_y = self.rect.y + 10
        # Iterate over a shallow copy to prevent concurrent modification exceptions
        for i, line in enumerate(list(self.history)):
            text_color = (0, 255, 200) if "Error" in line else (180, 200, 220)
            if line.startswith("> "):
                text_color = (255, 255, 255)
            
            txt_surf = get_cached_text(font, line, text_color)
            surface.blit(txt_surf, (self.rect.x + 10, start_y + i * line_height))

        # Draw input line prompt
        prompt_y = self.rect.bottom - 30
        pygame.draw.line(surface, (40, 50, 70), (self.rect.x + 10, prompt_y - 5), (self.rect.right - 10, prompt_y - 5), 1)

        input_prompt = f"> {self.input_text}"
        # Add blinking cursor
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            input_prompt += "_"
        
        input_surf = get_cached_text(font, input_prompt, (255, 255, 255))
        surface.blit(input_surf, (self.rect.x + 10, prompt_y))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handles event capturing. Returns a command string to execute if Enter is pressed."""
        if not self.active:
            # Look for activation keys: backtick (`) or Tab
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_BACKQUOTE, pygame.K_TAB):
                    self.toggle()
                    return None
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_BACKQUOTE, pygame.K_TAB, pygame.K_ESCAPE):
                self.toggle()
                return None

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]

            elif event.key == pygame.K_RETURN:
                cmd = self.input_text.strip()
                if cmd:
                    self.log(f"> {cmd}")
                    self.command_history.append(cmd)
                    self.history_index = len(self.command_history)
                    self.input_text = ""
                    return cmd
                self.input_text = ""

            elif event.key == pygame.K_UP:
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.input_text = self.command_history[self.history_index]

            elif event.key == pygame.K_DOWN:
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_text = self.command_history[self.history_index]
                else:
                    self.history_index = len(self.command_history)
                    self.input_text = ""

            else:
                # Capture text input unicode
                if event.unicode and event.unicode.isprintable() and event.unicode not in ('`', '\t', '\r'):
                    self.input_text += event.unicode

        # Consume all key events when console is active
        return None


