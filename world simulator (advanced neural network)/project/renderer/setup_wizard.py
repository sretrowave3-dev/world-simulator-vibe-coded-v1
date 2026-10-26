"""
project/renderer/setup_wizard.py

Minimalistic, Sleek First-Time Setup Wizard for World Simulator.
Triggers automatically on first boot when no user profile or saves exist.
Presents a modern, intuitive 4-step wizard:
1. Preferences & Visuals
2. Privacy & Telemetry Consent (Free, Open-Source & Safe)
3. Gemini Cognition & Multi-Key Routing (with prominent Skip / Run Offline option)
4. Git-Like Save Protection & Launch
"""

from __future__ import annotations

import os
import sys
import time
import json
import pygame
from typing import Dict, Any, List, Optional, Tuple
from project.core.user_profile import user_profile_manager, UserProfile
from project.core.telemetry_dispatcher import telemetry_dispatcher


# Minimalist Dark Slate Theme Palette
COLOR_BG          = (13, 17, 23)        # #0D1117 Deep Charcoal
COLOR_CARD        = (22, 27, 34)        # #161B22 Card container
COLOR_CARD_BORDER = (48, 54, 61)        # #30363D Subtle border
COLOR_TEXT_MAIN   = (230, 237, 243)    # #E6EDF3 Crisp text
COLOR_TEXT_MUTED  = (139, 148, 158)    # #8B949E Subdued text
COLOR_ACCENT_CYAN = (88, 166, 255)     # #58A6FF Primary blue/cyan
COLOR_ACCENT_GRN  = (63, 185, 80)      # #3FB950 Success emerald
COLOR_ACCENT_WARN = (210, 153, 34)     # #D29922 Amber
COLOR_ACCENT_RED  = (248, 81, 73)      # #F85149 Red delete
COLOR_INPUT_BG    = (33, 38, 45)       # #21262D Input field
COLOR_HOVER       = (40, 46, 56)


class TextInput:
    """Clean minimalist text input field with selection, cursor, and clipboard paste."""

    def __init__(self, x: int, y: int, width: int, height: int, placeholder: str = "", default_text: str = "") -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.text = default_text
        self.active = False
        self.cursor_visible = True
        self.last_blink = time.time()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        border_col = COLOR_ACCENT_CYAN if self.active else COLOR_CARD_BORDER
        pygame.draw.rect(surface, COLOR_INPUT_BG, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, 1, border_radius=6)

        display_text = self.text if self.text else self.placeholder
        text_col = COLOR_TEXT_MAIN if self.text else COLOR_TEXT_MUTED
        txt_surf = font.render(display_text, True, text_col)
        
        # Bounded text blit
        surface.blit(txt_surf, (self.rect.x + 12, self.rect.y + (self.rect.height - txt_surf.get_height()) // 2))

        # Blinking cursor
        if self.active:
            if time.time() - self.last_blink > 0.4:
                self.cursor_visible = not self.cursor_visible
                self.last_blink = time.time()
            if self.cursor_visible:
                cx = self.rect.x + 12 + font.size(self.text)[0] + 2
                cy = self.rect.y + 7
                ch = self.rect.height - 14
                pygame.draw.line(surface, COLOR_TEXT_MAIN, (cx, cy), (cx, cy + ch), 2)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return self.active

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_GUI):
                # Paste clipboard
                try:
                    pasted = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if pasted:
                        if isinstance(pasted, bytes):
                            pasted = pasted.decode("utf-8", errors="ignore").replace("\x00", "")
                        self.text += str(pasted).strip()
                        return True
                except Exception:
                    pass
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                if event.unicode and event.unicode.isprintable():
                    self.text += event.unicode
                    return True
        return False


class SetupButton:
    """Minimalist rounded button."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, callback, style: str = "default") -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.style = style  # "primary", "default", "success", "danger", "outline"
        self.is_hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.style == "primary":
            bg = (70, 140, 240) if self.is_hovered else COLOR_ACCENT_CYAN
            border = bg
            txt_col = (13, 17, 23)
        elif self.style == "success":
            bg = (50, 160, 70) if self.is_hovered else COLOR_ACCENT_GRN
            border = bg
            txt_col = (13, 17, 23)
        elif self.style == "danger":
            bg = (200, 60, 60) if self.is_hovered else COLOR_ACCENT_RED
            border = bg
            txt_col = (255, 255, 255)
        elif self.style == "outline":
            bg = COLOR_HOVER if self.is_hovered else COLOR_CARD
            border = COLOR_ACCENT_CYAN if self.is_hovered else COLOR_CARD_BORDER
            txt_col = COLOR_ACCENT_CYAN if self.is_hovered else COLOR_TEXT_MAIN
        else:
            bg = COLOR_HOVER if self.is_hovered else COLOR_CARD
            border = (80, 90, 105) if self.is_hovered else COLOR_CARD_BORDER
            txt_col = COLOR_TEXT_MAIN

        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=6)

        txt_surf = font.render(self.text, True, txt_col)
        tx = self.rect.x + (self.rect.width - txt_surf.get_width()) // 2
        ty = self.rect.y + (self.rect.height - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (tx, ty))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class OptionPillGroup:
    """Horizontal single-selection pill selector."""

    def __init__(self, x: int, y: int, label: str, options: List[str], default_idx: int = 0) -> None:
        self.x = x
        self.y = y
        self.label = label
        self.options = options
        self.selected_idx = default_idx
        self.buttons: List[Tuple[pygame.Rect, str]] = []
        self._layout()

    def _layout(self) -> None:
        self.buttons = []
        curr_x = self.x
        pill_height = 30
        for opt in self.options:
            pill_width = max(80, len(opt) * 9 + 24)
            rect = pygame.Rect(curr_x, self.y + 24, pill_width, pill_height)
            self.buttons.append((rect, opt))
            curr_x += pill_width + 10

    @property
    def selected_value(self) -> str:
        return self.options[self.selected_idx]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, label_font: pygame.font.Font) -> None:
        lbl_surf = label_font.render(self.label, True, COLOR_TEXT_MUTED)
        surface.blit(lbl_surf, (self.x, self.y))

        for idx, (rect, opt) in enumerate(self.buttons):
            is_sel = (idx == self.selected_idx)
            bg = COLOR_ACCENT_CYAN if is_sel else COLOR_CARD
            border = COLOR_ACCENT_CYAN if is_sel else COLOR_CARD_BORDER
            txt_col = (13, 17, 23) if is_sel else COLOR_TEXT_MAIN

            pygame.draw.rect(surface, bg, rect, border_radius=15)
            pygame.draw.rect(surface, border, rect, 1, border_radius=15)

            txt_surf = font.render(opt, True, txt_col)
            tx = rect.x + (rect.width - txt_surf.get_width()) // 2
            ty = rect.y + (rect.height - txt_surf.get_height()) // 2
            surface.blit(txt_surf, (tx, ty))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, (rect, _) in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    self.selected_idx = idx
                    return True
        return False


class FirstTimeSetupWizard:
    """Interactive Pygame Setup Wizard."""

    def __init__(self, screen_w: int = 1280, screen_h: int = 720) -> None:
        self.w = screen_w
        self.h = screen_h
        self.current_step = 1  # 1 to 4
        self.total_steps = 4

        # Stored state
        self.user_name = "Architect"
        self.resolution_idx = 0
        self.theme_idx = 0
        self.world_size_idx = 0
        self.pace_idx = 0

        # Consent & Telemetry
        self.telemetry_consent = False
        self.telemetry_mode = "local_only"
        self.webhook_url = ""

        # Gemini Cognition
        self.is_offline_selected = False
        self.api_keys: List[str] = []

        # Load existing keys from .env if present
        try:
            env_key = os.environ.get("GEMINI_API_KEY")
            if env_key and env_key.strip():
                self.api_keys.append(env_key.strip())
        except Exception:
            pass

        # Fonts
        font_cascade = "DejaVu Sans Mono,Ubuntu Mono,Consolas,Courier New,monospace"
        self.title_font = pygame.font.SysFont(font_cascade, 22, bold=True)
        self.head_font  = pygame.font.SysFont(font_cascade, 16, bold=True)
        self.body_font  = pygame.font.SysFont(font_cascade, 13)
        self.small_font = pygame.font.SysFont(font_cascade, 11)

        # UI Input components
        card_w = min(860, self.w - 100)
        card_x = (self.w - card_w) // 2
        card_y = 120

        # Tab 1 Components
        self.name_input = TextInput(card_x + 40, card_y + 70, 360, 36, placeholder="Your Callsign", default_text="Architect")
        self.pill_res = OptionPillGroup(card_x + 40, card_y + 130, "DISPLAY RESOLUTION", ["1280x720", "1600x900", "1920x1080"], 0)
        self.pill_theme = OptionPillGroup(card_x + 40, card_y + 210, "VISUAL THEME", ["Minimalist Slate", "Bioluminescent Dark", "High Contrast"], 0)
        self.pill_world = OptionPillGroup(card_x + 40, card_y + 290, "WORLD DIMENSIONS", ["Standard (4096x4096)", "Compact (2048x2048)", "Massive (8192x8192)"], 0)

        # Tab 2 Components
        self.pill_telemetry_level = OptionPillGroup(
            card_x + 40, card_y + 265, "RESEARCH WORLD DATA LEVEL",
            ["Summary Only", "Deep Ecosystem", "Full Dump (Everything)"], 2
        )
        self.webhook_input = TextInput(card_x + 40, card_y + 340, 520, 36, placeholder="Optional: Discord / REST Webhook (leave blank for developer default)", default_text="")

        # Tab 3 Components
        self.key_input = TextInput(card_x + 40, card_y + 160, 500, 36, placeholder="Paste Google Gemini API Key (AIzaSy...)")
        self.btn_add_key = SetupButton(card_x + 550, card_y + 160, 110, 36, "+ Add Key", self._add_key_clicked, style="primary")
        self.btn_skip_offline = SetupButton(card_x + 40, card_y + 360, 260, 42, "⚡ Skip / Run Completely Offline", self._skip_offline_clicked, style="outline")

        # Global Nav Buttons
        nav_y = self.h - 90
        self.btn_back = SetupButton(card_x, nav_y, 110, 38, "← Back", self._back_step, style="default")
        self.btn_next = SetupButton(card_x + card_w - 130, nav_y, 130, 38, "Next →", self._next_step, style="primary")
        self.btn_launch = SetupButton(card_x + card_w - 240, nav_y, 240, 42, "🚀 Launch Simulator", self._complete_wizard, style="success")

        self.finished = False
        self.result_profile: Optional[UserProfile] = None

    def _add_key_clicked(self) -> None:
        key = self.key_input.text.strip()
        if key and key not in self.api_keys:
            self.api_keys.append(key)
            self.key_input.text = ""
            self.is_offline_selected = False

    def _remove_key(self, idx: int) -> None:
        if 0 <= idx < len(self.api_keys):
            self.api_keys.pop(idx)
            if not self.api_keys:
                self.is_offline_selected = True

    def _skip_offline_clicked(self) -> None:
        self.is_offline_selected = True
        self.api_keys.clear()
        self._next_step()

    def _back_step(self) -> None:
        if self.current_step > 1:
            self.current_step -= 1

    def _next_step(self) -> None:
        if self.current_step == 1:
            self.user_name = self.name_input.text.strip() or "Architect"
        if self.current_step < self.total_steps:
            self.current_step += 1

    def _complete_wizard(self) -> None:
        # Determine resolution
        res_map = [(1280, 720), (1600, 900), (1920, 1080)]
        chosen_res = res_map[self.pill_res.selected_idx]

        theme_map = ["minimalist_dark", "bioluminescent", "high_contrast"]
        chosen_theme = theme_map[self.pill_theme.selected_idx]

        is_offline = self.is_offline_selected or (len(self.api_keys) == 0)
        world_levels = ["summary", "deep", "full"]
        chosen_world_level = world_levels[self.pill_telemetry_level.selected_idx] if self.telemetry_consent else "opt_out"

        setup_data = {
            "user_name": self.user_name,
            "display": {
                "width": chosen_res[0],
                "height": chosen_res[1],
                "theme": chosen_theme,
            },
            "privacy_and_telemetry": {
                "consent_given": self.telemetry_consent,
                "telemetry_mode": "webhook" if (self.telemetry_consent and self.webhook_input.text.strip()) else ("opt_in" if self.telemetry_consent else "opt_out"),
                "webhook_url": self.webhook_input.text.strip() if self.telemetry_consent else "",
                "world_data_level": chosen_world_level,
            },
            "gemini": {
                "is_offline": is_offline,
                "api_keys": self.api_keys,
                "routing_strategy": "best_health",
            },
            "git_save": {
                "active_branch": "main",
                "auto_stash_conflict": True,
                "max_history": 50,
            }
        }

        # Apply and save
        self.result_profile = user_profile_manager.complete_setup(setup_data)
        self.finished = True

    def run(self) -> UserProfile:
        """Main Pygame event loop for the setup wizard."""
        screen = pygame.display.set_mode((self.w, self.h), pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption("World Simulator — First-Time Configuration Wizard")
        clock = pygame.time.Clock()

        # Try initializing scrap for clipboard paste support
        try:
            pygame.scrap.init()
        except Exception:
            pass

        while not self.finished:
            dt = clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # User closed wizard without finishing; complete with offline defaults
                    self._complete_wizard()
                    return self.result_profile or user_profile_manager.get_profile()

                if event.type == pygame.VIDEORESIZE:
                    self.w = max(900, event.w)
                    self.h = max(600, event.h)
                    screen = pygame.display.set_mode((self.w, self.h), pygame.DOUBLEBUF | pygame.RESIZABLE)
                    # Recenter components
                    card_w = min(860, self.w - 100)
                    card_x = (self.w - card_w) // 2
                    self.name_input.rect.x = card_x + 40
                    self.pill_res.x = card_x + 40
                    self.pill_res._layout()
                    self.pill_theme.x = card_x + 40
                    self.pill_theme._layout()
                    self.pill_world.x = card_x + 40
                    self.pill_world._layout()
                    self.pill_telemetry_level.x = card_x + 40
                    self.pill_telemetry_level._layout()
                    self.webhook_input.rect.x = card_x + 40
                    self.key_input.rect.x = card_x + 40
                    self.btn_add_key.rect.x = card_x + 550
                    self.btn_skip_offline.rect.x = card_x + 40
                    nav_y = self.h - 90
                    self.btn_back.rect.x = card_x
                    self.btn_back.rect.y = nav_y
                    self.btn_next.rect.x = card_x + card_w - 130
                    self.btn_next.rect.y = nav_y
                    self.btn_launch.rect.x = card_x + card_w - 240
                    self.btn_launch.rect.y = nav_y

                # Global Nav
                if self.current_step > 1:
                    self.btn_back.handle_event(event)

                if self.current_step < self.total_steps:
                    self.btn_next.handle_event(event)
                else:
                    self.btn_launch.handle_event(event)

                # Tab-specific event handlers
                if self.current_step == 1:
                    self.name_input.handle_event(event)
                    self.pill_res.handle_event(event)
                    self.pill_theme.handle_event(event)
                    self.pill_world.handle_event(event)

                elif self.current_step == 2:
                    # Toggle consent box
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        card_w = min(860, self.w - 100)
                        card_x = (self.w - card_w) // 2
                        consent_rect = pygame.Rect(card_x + 40, 120 + 225, 24, 24)
                        if consent_rect.collidepoint(event.pos):
                            self.telemetry_consent = not self.telemetry_consent

                    if self.telemetry_consent:
                        self.pill_telemetry_level.handle_event(event)
                        self.webhook_input.handle_event(event)

                elif self.current_step == 3:
                    self.key_input.handle_event(event)
                    self.btn_add_key.handle_event(event)
                    self.btn_skip_offline.handle_event(event)

                    # Check delete buttons on key list
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        card_w = min(860, self.w - 100)
                        card_x = (self.w - card_w) // 2
                        del_x = card_x + 520
                        start_y = 120 + 215
                        for i in range(len(self.api_keys)):
                            del_rect = pygame.Rect(del_x, start_y + i * 32, 28, 24)
                            if del_rect.collidepoint(event.pos):
                                self._remove_key(i)
                                break

            # ----------------- DRAWING -----------------
            screen.fill(COLOR_BG)
            card_w = min(860, self.w - 100)
            card_x = (self.w - card_w) // 2
            card_y = 120
            card_h = self.h - 230

            # Wizard Header Title
            title_surf = self.title_font.render("WORLD SIMULATOR — INITIAL ENVIRONMENT SETUP", True, COLOR_TEXT_MAIN)
            screen.blit(title_surf, (card_x, 35))

            sub_surf = self.body_font.render("Configure your world parameters, cognitive engine, and privacy preferences.", True, COLOR_TEXT_MUTED)
            screen.blit(sub_surf, (card_x, 68))

            # Step Progress Tabs
            steps_labels = ["1. Display & World", "2. Privacy & Consent", "3. Gemini Cognition", "4. Save Guard & Launch"]
            tab_w = card_w // len(steps_labels)
            for idx, label in enumerate(steps_labels, 1):
                tx = card_x + (idx - 1) * tab_w
                is_active = (idx == self.current_step)
                is_done = (idx < self.current_step)
                tab_col = COLOR_ACCENT_CYAN if is_active else (COLOR_ACCENT_GRN if is_done else COLOR_CARD_BORDER)
                
                # Tab line
                pygame.draw.line(screen, tab_col, (tx, 96), (tx + tab_w - 10, 96), 3 if is_active else 1)
                
                txt_col = COLOR_TEXT_MAIN if is_active else COLOR_TEXT_MUTED
                txt = self.small_font.render(label, True, txt_col)
                screen.blit(txt, (tx, 102))

            # Main Card Box
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            pygame.draw.rect(screen, COLOR_CARD, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 1, border_radius=8)

            # Draw Current Step Content
            if self.current_step == 1:
                self._draw_step_1(screen, card_x, card_y)
            elif self.current_step == 2:
                self._draw_step_2(screen, card_x, card_y)
            elif self.current_step == 3:
                self._draw_step_3(screen, card_x, card_y)
            elif self.current_step == 4:
                self._draw_step_4(screen, card_x, card_y)

            # Draw Navigation Buttons
            if self.current_step > 1:
                self.btn_back.draw(screen, self.body_font)

            if self.current_step < self.total_steps:
                self.btn_next.draw(screen, self.body_font)
            else:
                self.btn_launch.draw(screen, self.head_font)

            pygame.display.flip()

        return self.result_profile or user_profile_manager.get_profile()

    def _draw_step_1(self, screen: pygame.Surface, cx: int, cy: int) -> None:
        """Step 1: Callsign, Resolution, Theme, World Dimensions."""
        h_surf = self.head_font.render("System & Environmental Preferences", True, COLOR_TEXT_MAIN)
        screen.blit(h_surf, (cx + 40, cy + 25))

        lbl = self.small_font.render("SIMULATION OBSERVER / ARCHITECT NAME", True, COLOR_TEXT_MUTED)
        screen.blit(lbl, (cx + 40, cy + 52))
        self.name_input.draw(screen, self.body_font)

        self.pill_res.draw(screen, self.body_font, self.small_font)
        self.pill_theme.draw(screen, self.body_font, self.small_font)
        self.pill_world.draw(screen, self.body_font, self.small_font)

    def _draw_step_2(self, screen: pygame.Surface, cx: int, cy: int) -> None:
        """Step 2: Free & Open-Source Safe Telemetry Consent."""
        h_surf = self.head_font.render("Privacy, Diagnostics & Open-Source Telemetry", True, COLOR_TEXT_MAIN)
        screen.blit(h_surf, (cx + 40, cy + 25))

        desc = [
            "World Simulator is a transparent open-source research sandbox.",
            "You can choose whether to share anonymized performance benchmarks and crash logs",
            "with the developer to assist in rapid bug resolution and optimization.",
        ]
        for i, line in enumerate(desc):
            s = self.body_font.render(line, True, COLOR_TEXT_MUTED)
            screen.blit(s, (cx + 40, cy + 55 + i * 20))

        # Guarantees Box
        g_rect = pygame.Rect(cx + 40, cy + 125, 550, 85)
        pygame.draw.rect(screen, (16, 21, 29), g_rect, border_radius=6)
        pygame.draw.rect(screen, (40, 50, 65), g_rect, 1, border_radius=6)

        g_title = self.head_font.render("🛡️ SAFETY & ZERO-LEAK GUARANTEES (FREE & OPEN SOURCE)", True, COLOR_ACCENT_GRN)
        screen.blit(g_title, (cx + 52, cy + 135))

        guarantees = [
            "• Zero PII: Random anonymous client hash. No hardware IDs, no MAC, no username.",
            "• Secret Masking: All API keys and paths (e.g. C:\\Users\\...) are strictly regex-scrubbed.",
            "• Free Analytics: Active user count & world states sent safely to owner's endpoint/Discord.",
        ]
        for i, g in enumerate(guarantees):
            s = self.small_font.render(g, True, COLOR_TEXT_MUTED)
            screen.blit(s, (cx + 52, cy + 158 + i * 16))

        # Consent Checkbox
        box_rect = pygame.Rect(cx + 40, cy + 225, 24, 24)
        pygame.draw.rect(screen, COLOR_INPUT_BG, box_rect, border_radius=4)
        border_col = COLOR_ACCENT_GRN if self.telemetry_consent else COLOR_CARD_BORDER
        pygame.draw.rect(screen, border_col, box_rect, 2, border_radius=4)

        if self.telemetry_consent:
            inner_rect = pygame.Rect(cx + 44, cy + 229, 16, 16)
            pygame.draw.rect(screen, COLOR_ACCENT_GRN, inner_rect, border_radius=2)

        lbl_consent = self.body_font.render("I consent to share active user count and simulation research state data (Opt-In)", True, COLOR_TEXT_MAIN)
        screen.blit(lbl_consent, (cx + 74, cy + 228))

        # Telemetry Level & Webhook fields (if consented)
        if self.telemetry_consent:
            self.pill_telemetry_level.draw(screen, self.body_font, self.small_font)
            lbl_hook = self.small_font.render("CUSTOM WEBHOOK DISPATCH (OPTIONAL — LEAVE BLANK FOR DEVELOPER DEFAULT)", True, COLOR_TEXT_MUTED)
            screen.blit(lbl_hook, (cx + 40, cy + 322))
            self.webhook_input.draw(screen, self.body_font)
        else:
            note = self.small_font.render("Status: Telemetry is strictly DISABLED. Zero outbound analytics or world data will leave this PC.", True, COLOR_ACCENT_WARN)
            screen.blit(note, (cx + 40, cy + 270))

    def _draw_step_3(self, screen: pygame.Surface, cx: int, cy: int) -> None:
        """Step 3: Gemini API & Multi-Key Routing, or 100% Offline."""
        h_surf = self.head_font.render("Gemini Deity Cognition & Multi-Key Intelligent Routing", True, COLOR_TEXT_MAIN)
        screen.blit(h_surf, (cx + 40, cy + 25))

        desc = [
            "Connect one or more Gemini API keys to bestow emergent reasoning and cosmic deity communion",
            "upon sovereign organism leaders.",
            "⚡ Dynamic Load Balancer: Automatically health-checks keys, routing each query to the fastest,",
            "lowest-latency, unexhausted key with instant failover on HTTP 429 quota exhaustion.",
        ]
        for i, line in enumerate(desc):
            s = self.body_font.render(line, True, COLOR_TEXT_MUTED)
            screen.blit(s, (cx + 40, cy + 55 + i * 20))

        # Input & Add button
        lbl_k = self.small_font.render("ENTER GEMINI API KEY", True, COLOR_TEXT_MUTED)
        screen.blit(lbl_k, (cx + 40, cy + 142))
        self.key_input.draw(screen, self.body_font)
        self.btn_add_key.draw(screen, self.body_font)

        # Added Keys List
        start_y = cy + 215
        if self.api_keys:
            k_head = self.small_font.render(f"ACTIVE MULTI-KEY ROTATION POOL ({len(self.api_keys)} registered):", True, COLOR_ACCENT_CYAN)
            screen.blit(k_head, (cx + 40, start_y))
            start_y += 20
            for i, key in enumerate(self.api_keys[:4]):
                masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "****"
                pill_rect = pygame.Rect(cx + 40, start_y + i * 28, 470, 24)
                pygame.draw.rect(screen, (26, 32, 42), pill_rect, border_radius=4)
                
                txt = self.body_font.render(f"Key #{i + 1}:  {masked}  [Active Health-Routing]", True, COLOR_TEXT_MAIN)
                screen.blit(txt, (cx + 50, start_y + i * 28 + 4))

                # Delete button [X]
                del_rect = pygame.Rect(cx + 520, start_y + i * 28, 28, 24)
                pygame.draw.rect(screen, COLOR_ACCENT_RED, del_rect, border_radius=4)
                x_txt = self.body_font.render("X", True, (255, 255, 255))
                screen.blit(x_txt, (cx + 529, start_y + i * 28 + 3))
        else:
            no_k = self.body_font.render("No API keys registered yet.", True, COLOR_TEXT_MUTED)
            screen.blit(no_k, (cx + 40, start_y))

        # Offline Skip Button
        self.btn_skip_offline.draw(screen, self.body_font)
        off_info = [
            "Prefer no API? Click above to run 100% OFFLINE with local neural heuristics.",
            "Guarantee: Absolutely no pseudo affinity meter will be calculated or displayed.",
        ]
        for i, line in enumerate(off_info):
            s = self.small_font.render(line, True, COLOR_ACCENT_WARN if i == 1 else COLOR_TEXT_MUTED)
            screen.blit(s, (cx + 315, cy + 365 + i * 18))

    def _draw_step_4(self, screen: pygame.Surface, cx: int, cy: int) -> None:
        """Step 4: Git-Like Save Guard Overview & Launch Summary."""
        h_surf = self.head_font.render("Git-Like Save Protection & Ready to Launch", True, COLOR_TEXT_MAIN)
        screen.blit(h_surf, (cx + 40, cy + 25))

        # Git Safeguard Card
        git_card = pygame.Rect(cx + 40, cy + 60, 560, 95)
        pygame.draw.rect(screen, (16, 24, 34), git_card, border_radius=6)
        pygame.draw.rect(screen, (35, 55, 80), git_card, 1, border_radius=6)

        git_title = self.head_font.render("🛡️ ACCIDENTAL OVERWRITE PREVENTION (ZERO DATA LOSS)", True, COLOR_ACCENT_CYAN)
        screen.blit(git_title, (cx + 55, cy + 70))

        git_points = [
            "• Stale Overwrite Guard: If saving over an existing file with higher tick progress or",
            "  divergent lineage, the prior state is automatically preserved in an immutable branch stash.",
            "• Complete Revision Graph: Track commits, timeline branches, and check out any past state.",
        ]
        for i, pt in enumerate(git_points):
            s = self.small_font.render(pt, True, COLOR_TEXT_MUTED)
            screen.blit(s, (cx + 55, cy + 95 + i * 16))

        # Configuration Summary Card
        sum_title = self.head_font.render("CONFIGURATION SUMMARY", True, COLOR_TEXT_MAIN)
        screen.blit(sum_title, (cx + 40, cy + 175))

        res_map = ["1280x720", "1600x900", "1920x1080"]
        theme_map = ["Minimalist Slate", "Bioluminescent Dark", "High Contrast"]

        is_offline = self.is_offline_selected or (len(self.api_keys) == 0)
        cog_str = "100% Offline (Local Neural Core — No Pseudo Affinity Meter)" if is_offline else f"Online ({len(self.api_keys)} Gemini API keys in router)"
        telem_str = "Consented (Scrubbed Diagnostics)" if self.telemetry_consent else "Opt-Out (Zero Telemetry)"

        summary_rows = [
            ("Observer Callsign:", self.user_name),
            ("Display Mode:", f"{res_map[self.pill_res.selected_idx]} ({theme_map[self.pill_theme.selected_idx]})"),
            ("Cognitive Engine:", cog_str),
            ("Diagnostics & Telemetry:", telem_str),
            ("Save Subsystem:", "Git-Protected Versioning (Auto-Stash on Divergence Enabled)"),
        ]

        for i, (k, v) in enumerate(summary_rows):
            k_surf = self.body_font.render(f"{k:<26}", True, COLOR_TEXT_MUTED)
            v_surf = self.body_font.render(v, True, COLOR_ACCENT_GRN if "Protected" in v or "Consented" in v or "Online" in v else COLOR_TEXT_MAIN)
            screen.blit(k_surf, (cx + 40, cy + 205 + i * 26))
            screen.blit(v_surf, (cx + 250, cy + 205 + i * 26))


def run_setup_wizard() -> UserProfile:
    """Convenience entry point to launch the first-time setup wizard."""
    wizard = FirstTimeSetupWizard()
    return wizard.run()
