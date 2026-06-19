"""
Modern self-drawn Pygame implementation of the Kaleidoscope app.

The rendering, layer, export, and history core are reused from the original
project. This file replaces the old pygame_gui-heavy shell with a compact,
custom UI that is easier to maintain and nicer to use.
"""
from __future__ import annotations

import datetime
import math
import os
import random
from collections import deque
from dataclasses import dataclass

import pygame

import config
import drawing
import utils
from export_manager import ExportManager
from history_manager import (
    AddLayerAction,
    AddPixelAction,
    AddShapeAction,
    ClearAllAction,
    DeleteLayerAction,
    DeleteShapesAction,
    HistoryManager,
    ModifyShapesAction,
)
from layer import Layer
from shapes import Arrow, Cross, Diamond, Heart, PolygonShape, Star, Triangle


@dataclass
class Slider:
    key: str
    rect: pygame.Rect
    label: str
    min_value: float
    max_value: float
    value: float
    decimals: int = 0

    def knob_x(self) -> int:
        span = self.max_value - self.min_value
        ratio = 0 if span == 0 else (self.value - self.min_value) / span
        return self.rect.left + round(max(0, min(1, ratio)) * self.rect.width)

    def set_from_x(self, x: int) -> None:
        ratio = (x - self.rect.left) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        self.value = self.min_value + ratio * (self.max_value - self.min_value)

    def value_text(self) -> str:
        if self.decimals <= 0:
            return str(int(round(self.value)))
        return f"{self.value:.{self.decimals}f}"


@dataclass
class Button:
    key: str
    rect: pygame.Rect
    label: str
    kind: str = "button"


class ModernApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Kaleidoscope Studio")
        self.clock = pygame.time.Clock()
        self.is_running = True

        self.canvas_rect = pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT)
        self.control_rect = pygame.Rect(config.DRAW_AREA_WIDTH, 0, config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT)
        self.layer_rect = pygame.Rect(
            config.DRAW_AREA_WIDTH + config.UI_PANEL_WIDTH,
            0,
            config.LAYER_PANEL_WIDTH,
            config.SCREEN_HEIGHT,
        )

        self.colors = {
            "bg": pygame.Color("#111318"),
            "panel": pygame.Color("#161a22"),
            "panel_2": pygame.Color("#202632"),
            "line": pygame.Color("#3a4354"),
            "text": pygame.Color("#f2efe7"),
            "muted": pygame.Color("#9aa3b2"),
            "accent": pygame.Color("#ffbf47"),
            "accent_2": pygame.Color("#23d3c3"),
            "danger": pygame.Color("#ff5a6a"),
            "green": pygame.Color("#8bd450"),
            "canvas": pygame.Color("#0c0d10"),
            "button": pygame.Color("#252d3a"),
            "button_hover": pygame.Color("#303a4b"),
            "button_dark": pygame.Color("#151923"),
            "button_edge": pygame.Color("#59657a"),
        }

        self.font_xs = self._load_font(14)
        self.font_sm = self._load_font(17)
        self.font_md = self._load_font(20, bold=True)
        self.font_lg = self._load_font(25, display=True)
        self.font_status = self._load_font(30, bold=True)
        self.tool_label_font = self._load_font(11)

        self.brush_type = "Line"
        self.brush_size = 3.2
        self.brush_spacing = 100.0
        self.brush_color_jitter = 0.0
        self.brush_flow = 30.0
        self.brush_size_jitter = 1.0
        self.spray_timer = 0.0
        self.user_path = []
        self.is_drawing = False

        self.active_tool = "brush"
        self.selected_shapes = []
        self.selection_mode = "point"
        self.preview_shape = None
        self.is_creating_shape = False
        self.creation_start_pos = None
        self.shape_drag_offset = None
        self.multi_shape_pre_drag_attrs = None
        self.is_lassoing = False
        self.lasso_points = []
        self.lasso_start_pos = None
        self.selected_shape_key = "triangle"
        self.next_shape_repeat_enabled = True

        self.num_slices = 12
        self.symmetry_mode = "Kaleidoscope"
        self.start_color = (255, 64, 196)
        self.end_color = (18, 223, 212)
        self.canvas_color = (12, 13, 16)
        self.active_color_selection = "start"

        self.enable_global_rotation = False
        self.global_rotation_angle = 0.0
        self.enable_object_rotation = False
        self.object_rotation_angle = 0.0
        self.enable_pulsing = False
        self.pulsing_scale = 1.0
        self.enable_trails = False
        self.trail_frames = deque(maxlen=15)
        self.guides_enabled = False
        self.lens_presets = {
            "calm": {
                "label": "Calm",
                "slices": 8,
                "symmetry_mode": "Rotate",
                "global_angle": 0.0,
                "object_angle": 0.0,
                "global_rotation": False,
                "object_rotation": False,
                "pulsing": False,
                "trails": False,
            },
            "bloom": {
                "label": "Bloom",
                "slices": 12,
                "symmetry_mode": "Kaleidoscope",
                "global_angle": 18.0,
                "object_angle": 0.0,
                "global_rotation": False,
                "object_rotation": False,
                "pulsing": True,
                "trails": False,
            },
            "prism": {
                "label": "Prism",
                "slices": 16,
                "symmetry_mode": "Kaleidoscope",
                "global_angle": 42.0,
                "object_angle": 36.0,
                "global_rotation": True,
                "object_rotation": True,
                "pulsing": True,
                "trails": True,
            },
        }
        self.active_lens_preset = None
        self.lens_transition = None

        self.layers = [Layer()]
        self.active_layer_index = 0
        self.history_manager = HistoryManager(self)
        self.export_manager = ExportManager()

        self.buttons: dict[str, Button] = {}
        self.sliders: dict[str, Slider] = {}
        self.layer_item_rects: list[tuple[pygame.Rect, int]] = []
        self.dragging_slider: str | None = None
        self.slider_drag_start_attrs = None
        self.slider_drag_center = None
        self.slider_drag_anchor_size = None
        self.spectrum_surface = utils.create_color_spectrum((190, 92))
        self.color_rect_start = pygame.Rect(0, 0, 1, 1)
        self.color_rect_end = pygame.Rect(0, 0, 1, 1)
        self.color_rect_bg = pygame.Rect(0, 0, 1, 1)
        self.spectrum_rect = pygame.Rect(0, 0, 1, 1)

        self.export_dialog_open = False
        self.export_filename = "kaleido_art_" + datetime.datetime.now().strftime("%H%M%S")
        self.export_format = "PNG"
        self.export_text_active = False

        self._build_static_ui()
        self._sync_sliders_from_state()

    def _load_font(self, size, bold=False, display=False):
        font_names = (
            ["CascadiaCode.ttf", "bahnschrift.ttf", "calibrib.ttf"]
            if display
            else ["bahnschrift.ttf", "segoeui.ttf", "calibri.ttf"]
        )
        if bold and not display:
            font_names = ["bahnschrift.ttf", "segoeuib.ttf", "calibrib.ttf"] + font_names
        for font_name in font_names:
            font_path = os.path.join("C:\\Windows\\Fonts", font_name)
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, size)
        return pygame.font.Font(None, size + 4)

    def _build_static_ui(self):
        self.buttons.clear()
        self.sliders.clear()

        panel_x = self.control_rect.left
        x = panel_x + 15
        y = 84
        tool_size = 38
        gap = 10
        for i, (key, label) in enumerate(
            [("brush", "Brush"), ("select", "Select"), ("shape", "Shape"), ("star", "Star")]
        ):
            self.buttons[f"tool:{key}"] = Button(
                f"tool:{key}",
                pygame.Rect(x + i * (tool_size + gap), y, tool_size, tool_size),
                label,
                "tool",
            )

        self.buttons["select_mode:point"] = Button("select_mode:point", pygame.Rect(x, 154, 92, 30), "Point", "segment")
        self.buttons["select_mode:lasso"] = Button("select_mode:lasso", pygame.Rect(x + 98, 154, 92, 30), "Lasso", "segment")

        y = 158
        for i, label in enumerate(["Line", "Circle", "Spray"]):
            self.buttons[f"brush_type:{label}"] = Button(
                f"brush_type:{label}",
                pygame.Rect(x + i * 64, y, 58, 30),
                label,
                "segment",
            )

        y = 215
        self.sliders["brush_size"] = Slider(
            "brush_size", pygame.Rect(x, y, 190, 8), "Size", 1, 10, self.brush_size, 1
        )
        self.sliders["brush_spacing"] = Slider(
            "brush_spacing", pygame.Rect(x, y + 48, 190, 8), "Spacing", 1, 300, self.brush_spacing
        )
        self.sliders["brush_color_jitter"] = Slider(
            "brush_color_jitter",
            pygame.Rect(x, y + 88, 190, 8),
            "Color jitter",
            0,
            100,
            self.brush_color_jitter * 100,
        )
        self.sliders["brush_flow"] = Slider(
            "brush_flow", pygame.Rect(x, y + 48, 190, 8), "Flow", 5, 100, self.brush_flow
        )
        self.sliders["brush_size_jitter"] = Slider(
            "brush_size_jitter",
            pygame.Rect(x, y + 88, 190, 8),
            "Size jitter",
            0,
            5,
            self.brush_size_jitter,
            1,
        )

        self.sliders["shape_size"] = Slider(
            "shape_size", pygame.Rect(x, 226, 190, 8), "Shape size", 10, 300, 50
        )
        self.sliders["shape_rotation"] = Slider(
            "shape_rotation", pygame.Rect(x, 274, 190, 8), "Rotation", 0, 360, 0
        )
        shape_buttons = [
            ("triangle", "Tri"),
            ("star", "Star"),
            ("circle", "Circle"),
            ("square", "Square"),
            ("diamond", "Dia"),
            ("hexagon", "Hex"),
            ("arrow", "Arrow"),
            ("cross", "Cross"),
            ("heart", "Heart"),
        ]
        for i, (key, label) in enumerate(shape_buttons):
            rect = pygame.Rect(x + (i % 3) * 64, 166 + (i // 3) * 36, 58, 30)
            self.buttons[f"shape_lib:{key}"] = Button(f"shape_lib:{key}", rect, label, "segment")
        self.buttons["shape_repeat"] = Button("shape_repeat", pygame.Rect(x, 276, 92, 30), "Repeat", "segment")
        self.buttons["shape_free"] = Button("shape_free", pygame.Rect(x + 98, 276, 92, 30), "Free", "segment")
        self.buttons["selected_repeat"] = Button("selected_repeat", pygame.Rect(x, 306, 92, 30), "Repeat", "segment")
        self.buttons["selected_free"] = Button("selected_free", pygame.Rect(x + 98, 306, 92, 30), "Free", "segment")
        self.buttons["delete_shape"] = Button("delete_shape", pygame.Rect(x, 338, 190, 32), "Delete shape")

        for i, (key, preset) in enumerate(self.lens_presets.items()):
            self.buttons[f"lens:{key}"] = Button(
                f"lens:{key}",
                pygame.Rect(x + i * 64, 378, 58, 30),
                preset["label"],
                "segment",
            )
        self.buttons["symmetry:Kaleidoscope"] = Button(
            "symmetry:Kaleidoscope", pygame.Rect(x, 414, 92, 30), "Mirror", "segment"
        )
        self.buttons["symmetry:Rotate"] = Button(
            "symmetry:Rotate", pygame.Rect(x + 98, 414, 92, 30), "Rotate", "segment"
        )
        self.sliders["slices"] = Slider("slices", pygame.Rect(x, 466, 190, 8), "Slices", 4, 16, self.num_slices)

        self.color_rect_start = pygame.Rect(x, 506, 58, 34)
        self.color_rect_end = pygame.Rect(x + 66, 506, 58, 34)
        self.color_rect_bg = pygame.Rect(x + 132, 506, 58, 34)
        self.spectrum_rect = pygame.Rect(x, 550, 190, 92)

        toggle_y = 680
        for i, (key, label) in enumerate(
            [
                ("global_rotation", "Global"),
                ("pulsing", "Pulse"),
                ("object_rotation", "Object"),
                ("trails", "Trail"),
            ]
        ):
            rect = pygame.Rect(x + (i % 2) * 98, toggle_y + (i // 2) * 38, 92, 30)
            self.buttons[f"toggle:{key}"] = Button(f"toggle:{key}", rect, label, "toggle")
        self.buttons["guides"] = Button("guides", pygame.Rect(x, 756, 92, 28), "Guides")
        self.buttons["export"] = Button("export", pygame.Rect(x + 102, 756, 88, 28), "Export")

        layer_x = self.layer_rect.left + 14
        self.buttons["add_layer"] = Button("add_layer", pygame.Rect(layer_x, 70, 152, 32), "Add layer")
        self.buttons["toggle_layer"] = Button("toggle_layer", pygame.Rect(layer_x, 624, 152, 30), "Toggle visible")
        self.buttons["delete_layer"] = Button("delete_layer", pygame.Rect(layer_x, 660, 152, 30), "Delete layer")
        self.buttons["clear_all"] = Button("clear_all", pygame.Rect(layer_x, 696, 152, 30), "Clear all")
        self.buttons["undo"] = Button("undo", pygame.Rect(layer_x, 744, 70, 32), "Undo")
        self.buttons["redo"] = Button("redo", pygame.Rect(layer_x + 82, 744, 70, 32), "Redo")

    def _sync_sliders_from_state(self):
        self.sliders["brush_size"].value = self.brush_size
        self.sliders["brush_spacing"].value = self.brush_spacing
        self.sliders["brush_color_jitter"].value = self.brush_color_jitter * 100
        self.sliders["brush_flow"].value = self.brush_flow
        self.sliders["brush_size_jitter"].value = self.brush_size_jitter
        self.sliders["slices"].value = self.num_slices
        if self.selected_shapes:
            self.sliders["shape_size"].value = self.selected_shapes[0].size
            self.sliders["shape_rotation"].value = self.selected_shapes[0].rotation % 360

    def _update_layer_list_ui(self):
        self.active_layer_index = max(0, min(self.active_layer_index, len(self.layers) - 1))

    def run(self):
        while self.is_running:
            time_delta_seconds = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self._update(time_delta_seconds)
            self._draw()

    def _handle_events(self):
        input_blocked = self.export_manager.is_active()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                continue

            if self.export_dialog_open:
                self._handle_export_dialog_event(event)
                continue

            if event.type == pygame.KEYDOWN and not input_blocked:
                self._handle_keydown(event)

            if input_blocked:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_down(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_mouse_up(event.pos)

    def _handle_keydown(self, event):
        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and self.selected_shapes:
            self._action_delete_selected_shape()
            return
        if event.mod & pygame.KMOD_CTRL:
            if event.key == pygame.K_z:
                self.history_manager.undo()
            elif event.key == pygame.K_y:
                self.history_manager.redo()

    def _handle_mouse_down(self, pos):
        self.dragging_slider = self._slider_at(pos)
        if self.dragging_slider:
            self._begin_slider_drag(self.dragging_slider)
            self._update_slider(self.dragging_slider, pos[0], commit=False)
            return

        button_key = self._button_at(pos)
        if button_key:
            self._activate_button(button_key)
            return

        layer_index = self._layer_at(pos)
        if layer_index is not None:
            self.active_layer_index = layer_index
            self._clear_selection()
            return

        color_event = self._handle_color_picker_click(pos)
        if color_event:
            return

        if self.canvas_rect.collidepoint(pos):
            if self.active_tool == "brush":
                self.is_drawing = True
                self.user_path = [{"pos": pos, "size": self.brush_size}]
            elif self.active_tool in ["shape", "star"]:
                self._start_shape_creation(pos)
            elif self.active_tool == "select":
                selection_bounds = self._selection_bounds()
                if selection_bounds and selection_bounds.inflate(12, 12).collidepoint(pos):
                    self._begin_selection_drag(pos)
                elif self.selection_mode == "lasso":
                    self._start_lasso(pos)
                else:
                    self._handle_selection(pos)

    def _handle_mouse_motion(self, event):
        if self.dragging_slider:
            self._update_slider(self.dragging_slider, event.pos[0], commit=False)
            return

        if self.is_drawing and self.canvas_rect.collidepoint(event.pos):
            self.user_path.append({"pos": event.pos, "size": self.brush_size})
        elif self.is_lassoing:
            self._update_lasso(event.pos)
        elif self.is_creating_shape:
            self._update_shape_creation(event.pos)
        elif self.selected_shapes and self.shape_drag_offset and event.buttons[0]:
            self._drag_selected_shapes(event.pos)

    def _handle_mouse_up(self, pos):
        if self.dragging_slider:
            self._update_slider(self.dragging_slider, pos[0], commit=True)
            self.dragging_slider = None
            self.slider_drag_start_attrs = None
            self.slider_drag_center = None
            self.slider_drag_anchor_size = None
            return
        if self.is_drawing:
            self._action_finish_drawing()
        elif self.is_lassoing:
            self._finish_lasso()
        elif self.is_creating_shape:
            self._finish_shape_creation()
        elif self.shape_drag_offset:
            self._finish_shape_drag()

    def _handle_export_dialog_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.export_text_active:
                if event.key == pygame.K_BACKSPACE:
                    self.export_filename = self.export_filename[:-1]
                elif event.key == pygame.K_RETURN:
                    self._action_start_export()
                elif event.key == pygame.K_ESCAPE:
                    self.export_dialog_open = False
                elif event.unicode and event.unicode not in '\\/:*?"<>|':
                    self.export_filename += event.unicode
            elif event.key == pygame.K_ESCAPE:
                self.export_dialog_open = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx = config.SCREEN_WIDTH // 2
            cy = config.SCREEN_HEIGHT // 2
            input_rect = pygame.Rect(cx - 180, cy - 36, 360, 34)
            png_rect = pygame.Rect(cx - 180, cy + 12, 168, 34)
            gif_rect = pygame.Rect(cx + 12, cy + 12, 168, 34)
            cancel_rect = pygame.Rect(cx - 180, cy + 70, 116, 36)
            export_rect = pygame.Rect(cx + 64, cy + 70, 116, 36)

            self.export_text_active = input_rect.collidepoint(event.pos)
            if png_rect.collidepoint(event.pos):
                self.export_format = "PNG"
            elif gif_rect.collidepoint(event.pos):
                self.export_format = "GIF"
            elif cancel_rect.collidepoint(event.pos):
                self.export_dialog_open = False
            elif export_rect.collidepoint(event.pos):
                self._action_start_export()

    def _slider_at(self, pos):
        for key in self._visible_slider_keys():
            slider = self.sliders[key]
            hit_rect = slider.rect.inflate(12, 22)
            if hit_rect.collidepoint(pos):
                return key
        return None

    def _button_at(self, pos):
        for key, button in self.buttons.items():
            if not self._button_visible(key):
                continue
            if button.rect.collidepoint(pos):
                return key
        return None

    def _layer_at(self, pos):
        for rect, index in self.layer_item_rects:
            if rect.collidepoint(pos):
                return index
        return None

    def _visible_slider_keys(self):
        keys = ["slices"]
        if self.active_tool == "brush":
            keys.append("brush_size")
            if self.brush_type == "Circle":
                keys.extend(["brush_spacing", "brush_color_jitter"])
            elif self.brush_type == "Spray":
                keys.extend(["brush_flow", "brush_size_jitter"])
        elif self.selected_shapes:
            keys.extend(["shape_size", "shape_rotation"])
        return keys

    def _button_visible(self, key):
        if key.startswith("brush_type:"):
            return self.active_tool == "brush"
        if key.startswith("select_mode:"):
            return self.active_tool == "select"
        if key.startswith("shape_lib:"):
            return self.active_tool in {"shape", "star"}
        if key in {"shape_repeat", "shape_free"}:
            return self.active_tool in {"shape", "star"}
        if key in {"selected_repeat", "selected_free"}:
            return bool(self.selected_shapes)
        if key == "delete_shape":
            return bool(self.selected_shapes)
        if key in {"undo", "redo"}:
            return True
        return True

    def _activate_button(self, key):
        if key.startswith("tool:"):
            self._set_active_tool(key.split(":", 1)[1])
            if key == "tool:star":
                self.selected_shape_key = "star"
        elif key.startswith("brush_type:"):
            self.brush_type = key.split(":", 1)[1]
        elif key.startswith("select_mode:"):
            self.selection_mode = key.split(":", 1)[1]
        elif key.startswith("shape_lib:"):
            self.selected_shape_key = key.split(":", 1)[1]
        elif key.startswith("lens:"):
            self._start_lens_transition(key.split(":", 1)[1])
        elif key == "shape_repeat":
            self.next_shape_repeat_enabled = True
            self._set_repeat_for_selection(True)
        elif key == "shape_free":
            self.next_shape_repeat_enabled = False
            self._set_repeat_for_selection(False)
        elif key == "selected_repeat":
            self._set_repeat_for_selection(True)
        elif key == "selected_free":
            self._set_repeat_for_selection(False)
        elif key.startswith("symmetry:"):
            self.symmetry_mode = key.split(":", 1)[1]
            self.active_lens_preset = None
            self.lens_transition = None
        elif key.startswith("toggle:"):
            self._toggle_effect(key.split(":", 1)[1])
        elif key == "guides":
            self.guides_enabled = not self.guides_enabled
        elif key == "export":
            self.export_dialog_open = True
            self.export_text_active = True
        elif key == "add_layer":
            self._action_add_new_layer()
        elif key == "toggle_layer":
            self.layers[self.active_layer_index].is_visible = not self.layers[self.active_layer_index].is_visible
        elif key == "delete_layer":
            self._action_delete_layer()
        elif key == "clear_all":
            self._action_clear_all()
        elif key == "undo":
            self.history_manager.undo()
        elif key == "redo":
            self.history_manager.redo()
        elif key == "delete_shape":
            self._action_delete_selected_shape()

    def _toggle_effect(self, key):
        self.active_lens_preset = None
        self.lens_transition = None
        if key == "global_rotation":
            self.enable_global_rotation = not self.enable_global_rotation
        elif key == "object_rotation":
            self.enable_object_rotation = not self.enable_object_rotation
        elif key == "pulsing":
            self.enable_pulsing = not self.enable_pulsing
        elif key == "trails":
            self.enable_trails = not self.enable_trails

    def _start_lens_transition(self, preset_key):
        preset = self.lens_presets[preset_key]
        self.active_lens_preset = preset_key
        self.symmetry_mode = preset["symmetry_mode"]
        self.enable_global_rotation = preset["global_rotation"]
        self.enable_object_rotation = preset["object_rotation"]
        self.enable_pulsing = preset["pulsing"]
        self.enable_trails = preset["trails"]
        if not self.enable_trails:
            self.trail_frames.clear()
        self.lens_transition = {
            "elapsed": 0.0,
            "duration": 0.55,
            "start_slices": float(self.num_slices),
            "target_slices": float(preset["slices"]),
            "start_global_angle": float(self.global_rotation_angle),
            "target_global_angle": float(preset["global_angle"]),
            "start_object_angle": float(self.object_rotation_angle),
            "target_object_angle": float(preset["object_angle"]),
        }

    def _update_lens_transition(self, time_delta_seconds):
        if not self.lens_transition:
            return
        self.lens_transition["elapsed"] += time_delta_seconds
        duration = self.lens_transition["duration"]
        t = min(1.0, self.lens_transition["elapsed"] / duration)
        eased = 1 - (1 - t) * (1 - t) * (1 - t)

        start_slices = self.lens_transition["start_slices"]
        target_slices = self.lens_transition["target_slices"]
        interpolated_slices = start_slices + (target_slices - start_slices) * eased
        rounded_slices = int(round(interpolated_slices))
        if rounded_slices % 2 == 1:
            rounded_slices += 1 if target_slices >= start_slices else -1
        self.num_slices = max(4, min(16, rounded_slices))

        self.global_rotation_angle = self._lerp_angle(
            self.lens_transition["start_global_angle"],
            self.lens_transition["target_global_angle"],
            eased,
        )
        self.object_rotation_angle = self._lerp_angle(
            self.lens_transition["start_object_angle"],
            self.lens_transition["target_object_angle"],
            eased,
        )

        if t >= 1.0:
            preset = self.lens_presets[self.active_lens_preset]
            self.num_slices = preset["slices"]
            self.global_rotation_angle = preset["global_angle"] % 360
            self.object_rotation_angle = preset["object_angle"] % 360
            self.lens_transition = None

    def _lerp_angle(self, start, target, t):
        delta = (target - start + 180) % 360 - 180
        return (start + delta * t) % 360

    def _set_repeat_for_selection(self, enabled):
        if not self.selected_shapes:
            return
        self._action_modify_selected_shape({"repeat_enabled": enabled})

    def _update_slider(self, key, x, commit):
        slider = self.sliders[key]
        slider.set_from_x(x)

        if key == "brush_size":
            self.brush_size = slider.value
        elif key == "brush_spacing":
            self.brush_spacing = slider.value
        elif key == "brush_color_jitter":
            self.brush_color_jitter = slider.value / 100.0
        elif key == "brush_flow":
            self.brush_flow = slider.value
        elif key == "brush_size_jitter":
            self.brush_size_jitter = slider.value
        elif key == "slices":
            value = int(round(slider.value))
            value = value if value % 2 == 0 else value - 1
            self.num_slices = max(4, value)
            slider.value = self.num_slices
            self.active_lens_preset = None
            self.lens_transition = None
        elif key == "shape_size" and self.selected_shapes:
            if commit:
                self._commit_current_shape_transform(["pos", "size"])
            else:
                self._preview_shape_size_change(slider.value)
        elif key == "shape_rotation" and self.selected_shapes:
            if commit:
                self._commit_shape_slider_change({"rotation": slider.value})
            else:
                for shape in self.selected_shapes:
                    shape.rotation = slider.value

    def _begin_slider_drag(self, key):
        if key == "shape_size" and self.selected_shapes:
            self.slider_drag_start_attrs = {
                shape: {"pos": pygame.Vector2(shape.pos), "size": shape.size}
                for shape in self.selected_shapes
            }
            bounds = self._selection_bounds()
            self.slider_drag_center = pygame.Vector2(bounds.center) if bounds else pygame.Vector2(0, 0)
            self.slider_drag_anchor_size = max(1.0, self.selected_shapes[0].size)
        elif key == "shape_rotation" and self.selected_shapes:
            self.slider_drag_start_attrs = {shape: {"rotation": shape.rotation} for shape in self.selected_shapes}
            self.slider_drag_center = None
            self.slider_drag_anchor_size = None
        else:
            self.slider_drag_start_attrs = None
            self.slider_drag_center = None
            self.slider_drag_anchor_size = None

    def _preview_shape_size_change(self, value):
        if not self.selected_shapes:
            return
        if len(self.selected_shapes) == 1:
            self.selected_shapes[0].size = value
            return
        old_attrs = self.slider_drag_start_attrs
        if not old_attrs:
            old_attrs = {
                shape: {"pos": pygame.Vector2(shape.pos), "size": shape.size}
                for shape in self.selected_shapes
            }
        center = self.slider_drag_center or pygame.Vector2(self._selection_bounds().center)
        anchor = self.slider_drag_anchor_size or max(1.0, self.selected_shapes[0].size)
        scale = max(0.05, value / anchor)
        for shape in self.selected_shapes:
            attrs = old_attrs.get(shape)
            if not attrs:
                continue
            old_pos = pygame.Vector2(attrs["pos"])
            shape.pos = center + (old_pos - center) * scale
            shape.size = max(1.0, attrs["size"] * scale)

    def _commit_current_shape_transform(self, attrs):
        if not self.selected_shapes:
            return
        old_attrs = self.slider_drag_start_attrs
        if not old_attrs:
            old_attrs = {
                shape: {attr: getattr(shape, attr) for attr in attrs}
                for shape in self.selected_shapes
            }
        changes = []
        for shape in self.selected_shapes:
            shape_old_attrs = old_attrs.get(shape)
            if not shape_old_attrs:
                continue
            shape_new_attrs = {attr: getattr(shape, attr) for attr in attrs}
            if any(shape_old_attrs.get(attr) != shape_new_attrs.get(attr) for attr in attrs):
                changes.append((shape, shape_old_attrs, shape_new_attrs))
        if changes:
            action = ModifyShapesAction(changes)
            self.history_manager.undo_stack.append(action)
            self.history_manager.redo_stack.clear()

    def _commit_shape_slider_change(self, new_attrs):
        if not self.selected_shapes:
            return
        old_attrs = self.slider_drag_start_attrs
        if not old_attrs:
            old_attrs = {shape: {key: getattr(shape, key) for key in new_attrs} for shape in self.selected_shapes}
        changes = []
        for shape in self.selected_shapes:
            shape_old_attrs = old_attrs.get(shape, {key: getattr(shape, key) for key in new_attrs})
            shape_new_attrs = dict(new_attrs)
            changes.append((shape, shape_old_attrs, shape_new_attrs))
        if any(old != new for _shape, old, new in changes):
            action = ModifyShapesAction(changes)
            self.history_manager.undo_stack.append(action)
            self.history_manager.redo_stack.clear()

    def _handle_color_picker_click(self, pos):
        if self.color_rect_start.collidepoint(pos):
            self.active_color_selection = "start"
            return True
        if self.color_rect_end.collidepoint(pos):
            self.active_color_selection = "end"
            return True
        if self.color_rect_bg.collidepoint(pos):
            self.active_color_selection = "background"
            return True
        if self.spectrum_rect.collidepoint(pos):
            local_pos = (pos[0] - self.spectrum_rect.left, pos[1] - self.spectrum_rect.top)
            picked_color = self.spectrum_surface.get_at(local_pos)
            color = (picked_color.r, picked_color.g, picked_color.b)
            if self.active_color_selection == "start":
                self.start_color = color
            elif self.active_color_selection == "end":
                self.end_color = color
            else:
                self.canvas_color = color
            if self.selected_shapes and self.active_color_selection != "background":
                self._action_modify_selected_shape({"stroke_color": color})
            return True
        return False

    def _clear_selection(self):
        for shape in self.selected_shapes:
            shape.selected = False
        self.selected_shapes = []
        self.shape_drag_offset = None
        self.multi_shape_pre_drag_attrs = None

    def _set_selection(self, shapes):
        self._clear_selection()
        self.selected_shapes = list(dict.fromkeys(shapes))
        for shape in self.selected_shapes:
            shape.selected = True
        self._sync_sliders_from_state()

    def _selection_bounds(self):
        if not self.selected_shapes:
            return None
        bounds = self.selected_shapes[0].get_bounding_box().copy()
        for shape in self.selected_shapes[1:]:
            bounds.union_ip(shape.get_bounding_box())
        return bounds

    def _start_lasso(self, pos):
        self.is_lassoing = True
        self.lasso_start_pos = pygame.Vector2(pos)
        self.lasso_points = [pygame.Vector2(pos)]

    def _update_lasso(self, pos):
        if self.canvas_rect.collidepoint(pos):
            point = pygame.Vector2(pos)
            if not self.lasso_points or point.distance_to(self.lasso_points[-1]) > 3:
                self.lasso_points.append(point)

    def _finish_lasso(self):
        if len(self.lasso_points) < 3:
            self.is_lassoing = False
            self.lasso_points = []
            return
        selected = []
        active_layer = self.layers[self.active_layer_index]
        for shape in active_layer.shapes:
            if self._shape_inside_lasso(shape):
                selected.append(shape)
        self._set_selection(selected)
        self.is_lassoing = False
        self.lasso_points = []
        self.lasso_start_pos = None

    def _begin_selection_drag(self, pos):
        if not self.selected_shapes:
            return
        self.shape_drag_offset = pygame.Vector2(pos) - self.selected_shapes[0].pos
        self.multi_shape_pre_drag_attrs = {
            shape: {"pos": pygame.Vector2(shape.pos)}
            for shape in self.selected_shapes
        }

    def _shape_inside_lasso(self, shape):
        box = shape.get_bounding_box()
        test_points = [
            pygame.Vector2(box.center),
            pygame.Vector2(box.topleft),
            pygame.Vector2(box.topright),
            pygame.Vector2(box.bottomleft),
            pygame.Vector2(box.bottomright),
        ]
        return any(self._point_in_polygon(point, self.lasso_points) for point in test_points)

    def _point_in_polygon(self, point, polygon):
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            pi = polygon[i]
            pj = polygon[j]
            if ((pi.y > point.y) != (pj.y > point.y)) and (
                point.x < (pj.x - pi.x) * (point.y - pi.y) / max(0.0001, pj.y - pi.y) + pi.x
            ):
                inside = not inside
            j = i
        return inside

    def _update(self, time_delta_seconds):
        if self.is_drawing and self.brush_type == "Spray":
            self.spray_timer += time_delta_seconds
            flow_interval = 1.0 / max(1.0, self.brush_flow)
            while self.spray_timer >= flow_interval:
                self.spray_timer -= flow_interval
                current_pos = pygame.mouse.get_pos()
                if self.canvas_rect.collidepoint(current_pos):
                    self.user_path.append({"pos": current_pos, "size": self.brush_size})

        if self.enable_global_rotation:
            self.global_rotation_angle = (self.global_rotation_angle - 0.5) % 360
        if self.enable_object_rotation:
            self.object_rotation_angle = (self.object_rotation_angle + 1.0) % 360
        self._update_lens_transition(time_delta_seconds)
        self.pulsing_scale = (
            1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.002)
            if self.enable_pulsing
            else 1.0
        )

        self._sync_sliders_from_state()
        self.export_manager.update()
        self.export_manager.update_timer(time_delta_seconds * 1000)

    def _draw(self):
        self.screen.fill(self.colors["bg"])
        pygame.draw.rect(self.screen, self.canvas_color, self.canvas_rect)

        composite_image = drawing.get_composite_image(
            self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle
        )

        if self.enable_trails:
            trail_copy = composite_image.copy()
            alpha = int(255 * (0.85 ** (len(self.trail_frames) + 1)))
            self.trail_frames.append((trail_copy, alpha))
        else:
            self.trail_frames.clear()

        final_image = drawing.apply_global_dynamics(
            composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames
        )
        if self.guides_enabled:
            drawing.draw_guide_lines(final_image, self.num_slices, self._guide_line_color())

        self.screen.blit(final_image, (0, 0))
        self._draw_canvas_overlays()
        self._draw_panels()
        self._draw_export_status()
        if self.export_dialog_open:
            self._draw_export_dialog()
        pygame.display.flip()

    def _draw_canvas_overlays(self):
        center = (config.CENTER_X, config.CENTER_Y)
        pygame.draw.circle(self.screen, pygame.Color(255, 255, 255, 38), center, 4, 1)

        if self.preview_shape:
            self.preview_shape.draw(self.screen)
        for shape in self.selected_shapes:
            pygame.draw.rect(self.screen, config.SELECTION_COLOR, shape.get_bounding_box(), 2)
        selection_bounds = self._selection_bounds()
        if selection_bounds and len(self.selected_shapes) > 1:
            pygame.draw.rect(self.screen, pygame.Color("#ffbf47"), selection_bounds.inflate(8, 8), 1, border_radius=4)
        if self.is_lassoing and len(self.lasso_points) > 1:
            pygame.draw.lines(self.screen, pygame.Color("#ffbf47"), False, self.lasso_points, 2)

        if self.is_drawing and len(self.user_path) > 1:
            points_to_draw = [p["pos"] for p in self.user_path]
            slice_angle_deg = 360 / self.num_slices
            center_vector = pygame.Vector2(config.CENTER_X, config.CENTER_Y)
            for i in range(self.num_slices):
                transformed_points = []
                for point in points_to_draw:
                    pos_relative_to_center = pygame.Vector2(point) - center_vector
                    rotated_pos = pos_relative_to_center.rotate(i * slice_angle_deg)
                    if self.symmetry_mode == "Kaleidoscope" and i % 2 == 1:
                        rotated_pos.y *= -1
                    transformed_points.append(rotated_pos + center_vector)
                pygame.draw.lines(self.screen, pygame.Color("#d8d3c8"), False, transformed_points, 2)

    def _draw_panels(self):
        pygame.draw.rect(self.screen, self.colors["panel"], self.control_rect)
        pygame.draw.rect(self.screen, self.colors["panel"], self.layer_rect)
        pygame.draw.line(self.screen, self.colors["line"], self.control_rect.topleft, self.control_rect.bottomleft)
        pygame.draw.line(self.screen, self.colors["line"], self.layer_rect.topleft, self.layer_rect.bottomleft)

        self._draw_control_panel()
        self._draw_layer_panel()

    def _draw_control_panel(self):
        x = self.control_rect.left + 15
        self._draw_text("Kaleido", (x, 14), self.font_lg, self.colors["text"])
        self._draw_text("Scope Studio", (x, 41), self.font_sm, self.colors["accent"])

        self._draw_section_label("Tools", 64)
        for key in ["tool:brush", "tool:select", "tool:shape", "tool:star"]:
            tool = key.split(":", 1)[1]
            is_active = self.active_tool == tool
            if key == "tool:star":
                is_active = self.active_tool == "shape" and self.selected_shape_key == "star"
            elif key == "tool:shape":
                is_active = self.active_tool == "shape" and self.selected_shape_key != "star"
            self._draw_button(self.buttons[key], active=is_active)
            label = self.buttons[key].label
            label_rect = pygame.Rect(self.buttons[key].rect.left - 6, self.buttons[key].rect.bottom + 3, self.buttons[key].rect.width + 12, 14)
            self._draw_text_center(label, label_rect, self.tool_label_font, pygame.Color("#b7c0cf"))

        if self.active_tool == "brush":
            self._draw_section_label("Brush", 137)
            for key in ["brush_type:Line", "brush_type:Circle", "brush_type:Spray"]:
                self._draw_button(self.buttons[key], active=self.brush_type == key.split(":", 1)[1])
            self._draw_slider(self.sliders["brush_size"])
            preview_center = (self.control_rect.right - 28, self.sliders["brush_size"].rect.centery)
            pygame.draw.circle(self.screen, self.start_color, preview_center, max(2, int(self.brush_size)))
            if self.brush_type == "Circle":
                self._draw_slider(self.sliders["brush_spacing"])
                self._draw_slider(self.sliders["brush_color_jitter"])
            elif self.brush_type == "Spray":
                self._draw_slider(self.sliders["brush_flow"])
                self._draw_slider(self.sliders["brush_size_jitter"])
        elif self.active_tool == "select":
            self._draw_section_label("Select", 137)
            for key in ["select_mode:point", "select_mode:lasso"]:
                self._draw_button(self.buttons[key], active=self.selection_mode == key.split(":", 1)[1])
            if self.selected_shapes:
                self._draw_selection_editor(x)
            else:
                help_text = "Click one shape." if self.selection_mode == "point" else "Draw around shapes."
                self._draw_text(help_text, (x, 215), self.font_sm, self.colors["muted"])
        elif self.active_tool in {"shape", "star"}:
            self._draw_section_label("Shape Library", 137)
            for key in [
                "shape_lib:triangle",
                "shape_lib:star",
                "shape_lib:circle",
                "shape_lib:square",
                "shape_lib:diamond",
                "shape_lib:hexagon",
                "shape_lib:arrow",
                "shape_lib:cross",
                "shape_lib:heart",
            ]:
                self._draw_button(self.buttons[key], active=self.selected_shape_key == key.split(":", 1)[1])
            self._draw_button(self.buttons["shape_repeat"], active=self.next_shape_repeat_enabled)
            self._draw_button(self.buttons["shape_free"], active=not self.next_shape_repeat_enabled)
        elif self.selected_shapes:
            self._draw_selection_editor(x)
        else:
            self._draw_section_label("Shape", 197)
            self._draw_text("Select a shape to edit it.", (x, 226), self.font_sm, self.colors["muted"])

        self._draw_section_label("Lens", 354)
        for key in ["lens:calm", "lens:bloom", "lens:prism"]:
            self._draw_button(self.buttons[key], active=self.active_lens_preset == key.split(":", 1)[1])
        for key in ["symmetry:Kaleidoscope", "symmetry:Rotate"]:
            self._draw_button(self.buttons[key], active=self.symmetry_mode == key.split(":", 1)[1])
        self._draw_slider(self.sliders["slices"])

        self._draw_section_label("Color", 482)
        self._draw_color_chip(self.color_rect_start, self.start_color, self.active_color_selection == "start")
        self._draw_color_chip(self.color_rect_end, self.end_color, self.active_color_selection == "end")
        self._draw_color_chip(self.color_rect_bg, self.canvas_color, self.active_color_selection == "background")
        self._draw_text_center("A", self.color_rect_start, self.font_xs, self._chip_text_color(self.start_color))
        self._draw_text_center("B", self.color_rect_end, self.font_xs, self._chip_text_color(self.end_color))
        self._draw_text_center("BG", self.color_rect_bg, self.font_xs, self._chip_text_color(self.canvas_color))
        self.screen.blit(self.spectrum_surface, self.spectrum_rect.topleft)
        pygame.draw.rect(self.screen, self.colors["line"], self.spectrum_rect, 1, border_radius=4)

        self._draw_section_label("Motion", 656)
        self._draw_button(self.buttons["toggle:global_rotation"], active=self.enable_global_rotation)
        self._draw_button(self.buttons["toggle:pulsing"], active=self.enable_pulsing)
        self._draw_button(self.buttons["toggle:object_rotation"], active=self.enable_object_rotation)
        self._draw_button(self.buttons["toggle:trails"], active=self.enable_trails)
        self._draw_button(self.buttons["guides"], active=self.guides_enabled)
        guide_text = "Off" if not self.guides_enabled else str(self.num_slices)
        self._draw_text(guide_text, (self.buttons["guides"].rect.right + 9, 761), self.font_xs, self.colors["muted"])
        self._draw_button(self.buttons["export"], active=False)

    def _draw_selection_editor(self, x, y_offset=197):
        title = "Selection" if len(self.selected_shapes) > 1 else "Shape"
        self._draw_section_label(title, y_offset)
        self._draw_text(f"{len(self.selected_shapes)} selected", (x, y_offset + 25), self.font_xs, self.colors["muted"])
        self._draw_slider(self.sliders["shape_size"])
        self._draw_slider(self.sliders["shape_rotation"])
        self._draw_button(self.buttons["selected_repeat"], active=all(getattr(s, "repeat_enabled", True) for s in self.selected_shapes))
        self._draw_button(self.buttons["selected_free"], active=all(not getattr(s, "repeat_enabled", True) for s in self.selected_shapes))
        self._draw_button(self.buttons["delete_shape"], danger=True)

    def _draw_layer_panel(self):
        x = self.layer_rect.left + 14
        self._draw_text("Layers", (x, 24), self.font_md, self.colors["text"])
        self._draw_text(f"{len(self.layers)} total", (x, 45), self.font_xs, self.colors["muted"])
        self._draw_button(self.buttons["add_layer"])

        self.layer_item_rects = []
        list_rect = pygame.Rect(x, 116, 152, 492)
        pygame.draw.rect(self.screen, self.colors["panel_2"], list_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors["line"], list_rect, 1, border_radius=8)

        item_y = list_rect.top + 8
        for index, layer in enumerate(self.layers[:12]):
            item_rect = pygame.Rect(list_rect.left + 8, item_y, list_rect.width - 16, 34)
            self.layer_item_rects.append((item_rect, index))
            active = index == self.active_layer_index
            fill = pygame.Color("#2d3340") if active else pygame.Color("#20252f")
            pygame.draw.rect(self.screen, fill, item_rect, border_radius=6)
            if active:
                pygame.draw.rect(self.screen, self.colors["accent"], item_rect, 1, border_radius=6)
            eye = "ON" if layer.is_visible else "OFF"
            self._draw_text(layer.name, (item_rect.left + 10, item_rect.top + 8), self.font_sm, self.colors["text"])
            self._draw_text(eye, (item_rect.right - 34, item_rect.top + 10), self.font_xs, self.colors["muted"])
            item_y += 39

        self._draw_button(self.buttons["toggle_layer"], active=self.layers[self.active_layer_index].is_visible)
        self._draw_button(self.buttons["delete_layer"], danger=len(self.layers) > 1)
        self._draw_button(self.buttons["clear_all"], danger=True)
        self._draw_button(self.buttons["undo"], active=self.history_manager.can_undo())
        self._draw_button(self.buttons["redo"], active=self.history_manager.can_redo())

    def _draw_section_label(self, text, y):
        x = self.control_rect.left + 15
        self._draw_text(text.upper(), (x, y), self.font_xs, pygame.Color("#b8c0cd"))
        pygame.draw.line(
            self.screen,
            self.colors["line"],
            (x + 72, y + 8),
            (self.control_rect.right - 15, y + 8),
        )

    def _draw_button(self, button, active=False, danger=False):
        mouse_pos = pygame.mouse.get_pos()
        hovered = button.rect.collidepoint(mouse_pos)
        base_rect = button.rect
        shadow_rect = base_rect.move(0, 2)

        if active:
            fill_top = self._mix_color(self.colors["accent"], pygame.Color("#fff1b8"), 0.35)
            fill_bottom = self.colors["accent"]
            text = pygame.Color("#131720")
            edge = pygame.Color("#ffe08a")
        elif danger:
            fill_top = pygame.Color("#522b36") if hovered else pygame.Color("#3a2229")
            fill_bottom = pygame.Color("#2c1820")
            text = self.colors["danger"]
            edge = pygame.Color("#7b3c49") if hovered else pygame.Color("#57313b")
        else:
            fill_top = self.colors["button_hover"] if hovered else self.colors["button"]
            fill_bottom = self.colors["button_dark"]
            text = self.colors["text"]
            edge = self.colors["button_edge"] if hovered else self.colors["line"]

        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0, 80), shadow_rect, border_radius=7)
        self._draw_vertical_gradient(base_rect, fill_top, fill_bottom, radius=7)
        pygame.draw.line(
            self.screen,
            self._mix_color(fill_top, pygame.Color("#ffffff"), 0.18),
            (base_rect.left + 7, base_rect.top + 1),
            (base_rect.right - 8, base_rect.top + 1),
        )
        pygame.draw.rect(self.screen, edge, base_rect, 1, border_radius=7)

        if active:
            indicator = pygame.Rect(base_rect.left + 7, base_rect.bottom - 4, base_rect.width - 14, 2)
            pygame.draw.rect(self.screen, pygame.Color("#111318"), indicator, border_radius=2)

        icon = self._button_icon(button)
        icon_only = button.kind == "tool"
        text_rect = base_rect.copy()
        if icon:
            self._draw_button_icon(icon, base_rect, text, centered=icon_only)
            if not icon_only:
                offset = 16 if base_rect.width <= 92 else 12
                text_rect.x += offset
                text_rect.width -= offset
        if not icon_only:
            self._draw_text_center(button.label, text_rect, self.font_sm, text)

    def _draw_slider(self, slider):
        label_pos = (slider.rect.left, slider.rect.top - 23)
        self._draw_text(slider.label, label_pos, self.font_xs, self.colors["muted"])
        self._draw_text(
            slider.value_text(),
            (slider.rect.right - 38, slider.rect.top - 23),
            self.font_xs,
            self.colors["text"],
        )
        pygame.draw.rect(self.screen, pygame.Color("#2b303b"), slider.rect, border_radius=5)
        fill_rect = pygame.Rect(slider.rect.left, slider.rect.top, slider.knob_x() - slider.rect.left, slider.rect.height)
        pygame.draw.rect(self.screen, self.colors["accent_2"], fill_rect, border_radius=5)
        pygame.draw.circle(self.screen, self.colors["text"], (slider.knob_x(), slider.rect.centery), 8)
        pygame.draw.circle(self.screen, pygame.Color("#111318"), (slider.knob_x(), slider.rect.centery), 4)

    def _draw_vertical_gradient(self, rect, top_color, bottom_color, radius=0):
        height = max(1, rect.height)
        gradient = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(height):
            color = self._mix_color(top_color, bottom_color, y / max(1, height - 1))
            pygame.draw.line(gradient, color, (0, y), (rect.width, y))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(gradient, rect.topleft)

    def _mix_color(self, color_a, color_b, t):
        t = max(0.0, min(1.0, t))
        return pygame.Color(
            int(color_a.r * (1 - t) + color_b.r * t),
            int(color_a.g * (1 - t) + color_b.g * t),
            int(color_a.b * (1 - t) + color_b.b * t),
            int(color_a.a * (1 - t) + color_b.a * t),
        )

    def _button_icon(self, button):
        return {
            "tool:brush": "brush",
            "tool:select": "select",
            "tool:shape": "shape",
            "tool:star": "star",
            "export": "export",
            "add_layer": "plus",
            "delete_layer": "minus",
            "clear_all": "clear",
            "undo": "undo",
            "redo": "redo",
            "guides": "guides",
        }.get(button.key)

    def _draw_button_icon(self, icon, rect, color, centered=False):
        cx = rect.centerx if centered else rect.left + 13
        cy = rect.centery
        if icon == "brush":
            pygame.draw.line(self.screen, color, (cx - 4, cy + 5), (cx + 5, cy - 4), 2)
            pygame.draw.circle(self.screen, color, (cx - 5, cy + 6), 3)
        elif icon == "select":
            pygame.draw.ellipse(self.screen, color, pygame.Rect(cx - 8, cy - 6, 14, 10), 2)
            pygame.draw.line(self.screen, color, (cx + 4, cy + 3), (cx + 9, cy + 8), 2)
        elif icon == "triangle":
            pygame.draw.polygon(self.screen, color, [(cx, cy - 7), (cx - 7, cy + 6), (cx + 7, cy + 6)], 2)
        elif icon == "shape":
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 7, cy - 7, 11, 11), 2, border_radius=2)
            pygame.draw.circle(self.screen, color, (cx + 5, cy + 5), 5, 2)
        elif icon == "star":
            points = []
            for i in range(10):
                radius = 8 if i % 2 == 0 else 3
                angle = math.radians(i * 36 - 90)
                points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            pygame.draw.polygon(self.screen, color, points, 1)
        elif icon == "export":
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 6, cy + 1, 12, 7), 1, border_radius=2)
            pygame.draw.line(self.screen, color, (cx, cy - 7), (cx, cy + 3), 2)
            pygame.draw.line(self.screen, color, (cx - 4, cy - 1), (cx, cy + 3), 2)
            pygame.draw.line(self.screen, color, (cx + 4, cy - 1), (cx, cy + 3), 2)
        elif icon == "plus":
            pygame.draw.line(self.screen, color, (cx - 6, cy), (cx + 6, cy), 2)
            pygame.draw.line(self.screen, color, (cx, cy - 6), (cx, cy + 6), 2)
        elif icon == "minus":
            pygame.draw.line(self.screen, color, (cx - 6, cy), (cx + 6, cy), 2)
        elif icon == "clear":
            pygame.draw.circle(self.screen, color, (cx, cy), 6, 1)
            pygame.draw.line(self.screen, color, (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
        elif icon == "undo":
            pygame.draw.arc(self.screen, color, pygame.Rect(cx - 7, cy - 6, 14, 12), 0.7, 5.3, 2)
            pygame.draw.line(self.screen, color, (cx - 6, cy - 3), (cx - 10, cy - 3), 2)
        elif icon == "redo":
            pygame.draw.arc(self.screen, color, pygame.Rect(cx - 7, cy - 6, 14, 12), -2.1, 2.5, 2)
            pygame.draw.line(self.screen, color, (cx + 6, cy - 3), (cx + 10, cy - 3), 2)
        elif icon == "guides":
            pygame.draw.circle(self.screen, color, (cx, cy), 7, 1)
            pygame.draw.line(self.screen, color, (cx, cy - 8), (cx, cy + 8), 1)
            pygame.draw.line(self.screen, color, (cx - 8, cy), (cx + 8, cy), 1)

    def _draw_color_chip(self, rect, color, active):
        pygame.draw.rect(self.screen, color, rect, border_radius=7)
        border_color = self.colors["accent"] if active else self.colors["line"]
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=7)

    def _chip_text_color(self, color):
        r, g, b = color[:3]
        return pygame.Color("#111318") if (r * 0.299 + g * 0.587 + b * 0.114) > 150 else self.colors["text"]

    def _guide_line_color(self):
        r, g, b = self.canvas_color[:3]
        complement = pygame.Color(255 - r, 255 - g, 255 - b)
        brightness = r * 0.299 + g * 0.587 + b * 0.114
        if brightness > 150:
            complement.hsva = (complement.hsva[0], min(85, complement.hsva[1] + 25), 28, 100)
        else:
            complement.hsva = (complement.hsva[0], min(90, complement.hsva[1] + 25), 92, 100)
        return complement

    def _with_canvas_background(self, surface):
        output = pygame.Surface(surface.get_size())
        output.fill(self.canvas_color)
        output.blit(surface, (0, 0))
        return output

    def _draw_export_status(self):
        message, progress = self.export_manager.get_status()
        if not message:
            return
        text_surf = self.font_status.render(message, True, self.colors["text"])
        text_rect = text_surf.get_rect(center=(config.DRAW_AREA_WIDTH // 2, 42))
        bg_rect = text_rect.inflate(28, 24)
        overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        overlay.fill((15, 17, 22, 220))
        self.screen.blit(overlay, bg_rect.topleft)
        pygame.draw.rect(self.screen, self.colors["accent"], bg_rect, 1, border_radius=10)
        self.screen.blit(text_surf, text_rect)
        if self.export_manager.state in ["rendering_gif", "saving_gif"]:
            bar_rect = pygame.Rect(bg_rect.left + 14, bg_rect.bottom + 8, bg_rect.width - 28, 8)
            pygame.draw.rect(self.screen, pygame.Color("#303644"), bar_rect, border_radius=4)
            fill = pygame.Rect(bar_rect.left, bar_rect.top, int(bar_rect.width * progress), bar_rect.height)
            pygame.draw.rect(self.screen, self.colors["accent_2"], fill, border_radius=4)

    def _draw_export_dialog(self):
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx = config.SCREEN_WIDTH // 2
        cy = config.SCREEN_HEIGHT // 2
        dialog = pygame.Rect(cx - 220, cy - 140, 440, 280)
        pygame.draw.rect(self.screen, pygame.Color("#181c24"), dialog, border_radius=12)
        pygame.draw.rect(self.screen, self.colors["accent"], dialog, 1, border_radius=12)
        self._draw_text("Export artwork", (dialog.left + 40, dialog.top + 30), self.font_md, self.colors["text"])

        input_rect = pygame.Rect(cx - 180, cy - 36, 360, 34)
        pygame.draw.rect(self.screen, pygame.Color("#252a34"), input_rect, border_radius=7)
        border = self.colors["accent"] if self.export_text_active else self.colors["line"]
        pygame.draw.rect(self.screen, border, input_rect, 1, border_radius=7)
        self._draw_text(self.export_filename, (input_rect.left + 10, input_rect.top + 8), self.font_sm, self.colors["text"])

        png_rect = pygame.Rect(cx - 180, cy + 12, 168, 34)
        gif_rect = pygame.Rect(cx + 12, cy + 12, 168, 34)
        self._draw_dialog_choice(png_rect, "PNG image", self.export_format == "PNG")
        self._draw_dialog_choice(gif_rect, "GIF animation", self.export_format == "GIF")

        cancel = Button("cancel", pygame.Rect(cx - 180, cy + 70, 116, 36), "Cancel")
        export = Button("confirm", pygame.Rect(cx + 64, cy + 70, 116, 36), "Export")
        self._draw_button(cancel)
        self._draw_button(export, active=True)

    def _draw_dialog_choice(self, rect, label, active):
        pygame.draw.rect(self.screen, self.colors["accent"] if active else pygame.Color("#252a34"), rect, border_radius=7)
        pygame.draw.rect(self.screen, self.colors["line"], rect, 1, border_radius=7)
        color = pygame.Color("#111318") if active else self.colors["text"]
        self._draw_text_center(label, rect, self.font_sm, color)

    def _draw_text(self, text, pos, font, color):
        surf = font.render(str(text), True, color)
        self.screen.blit(surf, pos)

    def _draw_text_center(self, text, rect, font, color):
        surf = font.render(str(text), True, color)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def _set_active_tool(self, tool_name):
        if tool_name == "star":
            tool_name = "shape"
            self.selected_shape_key = "star"
        self.active_tool = tool_name
        if tool_name != "select":
            self._clear_selection()

    def _start_shape_creation(self, pos):
        self.is_creating_shape = True
        self.creation_start_pos = pos
        stroke_color = self.start_color
        stroke_width = self.brush_size
        fill_color = (0, 0, 0, 0)
        self.preview_shape = self._create_shape(
            self.selected_shape_key,
            pos,
            1,
            fill_color,
            stroke_width,
            stroke_color,
            self.next_shape_repeat_enabled,
        )

    def _create_shape(self, shape_key, pos, size, fill_color, stroke_width, stroke_color, repeat_enabled):
        kwargs = {
            "stroke_width": stroke_width,
            "stroke_color": stroke_color,
            "repeat_enabled": repeat_enabled,
        }
        if shape_key == "triangle":
            return Triangle(pos, size, fill_color, **kwargs)
        if shape_key == "star":
            return Star(pos, size, fill_color, **kwargs)
        if shape_key == "circle":
            return PolygonShape(pos, size, fill_color, sides=32, **kwargs)
        if shape_key == "square":
            return PolygonShape(pos, size, fill_color, sides=4, **kwargs)
        if shape_key == "diamond":
            return Diamond(pos, size, fill_color, **kwargs)
        if shape_key == "hexagon":
            return PolygonShape(pos, size, fill_color, sides=6, **kwargs)
        if shape_key == "arrow":
            return Arrow(pos, size, fill_color, **kwargs)
        if shape_key == "cross":
            return Cross(pos, size, fill_color, **kwargs)
        if shape_key == "heart":
            return Heart(pos, size, fill_color, **kwargs)
        return Triangle(pos, size, fill_color, **kwargs)

    def _update_shape_creation(self, pos):
        if not self.preview_shape:
            return
        self.preview_shape.size = pygame.Vector2(pos).distance_to(self.creation_start_pos)
        self.preview_shape.pos = pygame.Vector2(self.creation_start_pos)

    def _finish_shape_creation(self):
        if not self.preview_shape or self.preview_shape.size < 5:
            self.is_creating_shape = False
            self.preview_shape = None
            return
        action = AddShapeAction(self.layers[self.active_layer_index], self.preview_shape)
        self.history_manager.execute_action(action)
        self.is_creating_shape = False
        self.preview_shape = None

    def _handle_selection(self, pos):
        self._clear_selection()
        click_pos_vec = pygame.Vector2(pos)
        center_vector = pygame.Vector2(config.CENTER_X, config.CENTER_Y)
        slice_angle_deg = 360 / self.num_slices
        active_layer = self.layers[self.active_layer_index]
        if not active_layer.is_visible:
            return

        for shape in reversed(active_layer.shapes):
            repeat_count = self.num_slices if getattr(shape, "repeat_enabled", True) else 1
            for i in range(repeat_count):
                pos_relative_to_center = click_pos_vec - center_vector
                if self.symmetry_mode == "Kaleidoscope" and i % 2 == 1:
                    pos_relative_to_center.y *= -1
                test_pos = pos_relative_to_center.rotate(-(i * slice_angle_deg)) + center_vector
                if shape.get_bounding_box().collidepoint(test_pos):
                    self._set_selection([shape])
                    self.shape_drag_offset = test_pos - shape.pos
                    self.multi_shape_pre_drag_attrs = {shape: {"pos": pygame.Vector2(shape.pos)}}
                    self._sync_sliders_from_state()
                    return

    def _drag_selected_shapes(self, pos):
        if not self.selected_shapes or not self.shape_drag_offset:
            return
        target = pygame.Vector2(pos) - self.shape_drag_offset
        first_shape = self.selected_shapes[0]
        delta = target - first_shape.pos
        for shape in self.selected_shapes:
            shape.pos += delta

    def _finish_shape_drag(self):
        if not self.selected_shapes or not self.multi_shape_pre_drag_attrs:
            return
        changes = []
        for shape in self.selected_shapes:
            old_attrs = self.multi_shape_pre_drag_attrs.get(shape)
            if not old_attrs:
                continue
            new_attrs = {"pos": pygame.Vector2(shape.pos)}
            if old_attrs["pos"] != new_attrs["pos"]:
                changes.append((shape, old_attrs, new_attrs))
        if changes:
            action = ModifyShapesAction(changes)
            self.history_manager.execute_action(action)
        self.shape_drag_offset = None
        self.multi_shape_pre_drag_attrs = None

    def _action_modify_selected_shape(self, new_attrs):
        if not self.selected_shapes:
            return
        changes = []
        for shape in self.selected_shapes:
            old_attrs = {key: getattr(shape, key) for key in new_attrs}
            changes.append((shape, old_attrs, dict(new_attrs)))
        action = ModifyShapesAction(changes)
        self.history_manager.execute_action(action)

    def _action_delete_selected_shape(self):
        if not self.selected_shapes:
            return
        action = DeleteShapesAction(self.layers[self.active_layer_index], self.selected_shapes)
        self.history_manager.execute_action(action)
        self._clear_selection()

    def _action_add_new_layer(self):
        new_layer = Layer()
        action = AddLayerAction(self, new_layer)
        self.history_manager.execute_action(action)

    def _action_delete_layer(self):
        if len(self.layers) <= 1:
            return
        layer_to_delete = self.layers[self.active_layer_index]
        index = self.active_layer_index
        action = DeleteLayerAction(self, layer_to_delete, index)
        self.history_manager.execute_action(action)

    def _action_clear_all(self):
        if not self.layers:
            return
        action = ClearAllAction(self, list(self.layers))
        self.history_manager.execute_action(action)
        self._clear_selection()

    def _action_finish_drawing(self):
        if not self.user_path:
            self.is_drawing = False
            self.spray_timer = 0.0
            return

        elements_to_draw = []
        path_len = len(self.user_path)
        path_length_pixels = 0
        if path_len >= 2:
            path_length_pixels = sum(
                pygame.Vector2(self.user_path[i + 1]["pos"]).distance_to(self.user_path[i]["pos"])
                for i in range(path_len - 1)
            )

        if self.brush_type == "Line":
            if path_len >= 2 and path_length_pixels > 0:
                current_dist = 0
                for i in range(path_len - 1):
                    p1, p2 = self.user_path[i], self.user_path[i + 1]
                    dist = pygame.Vector2(p2["pos"]).distance_to(p1["pos"])
                    steps = max(1, int(dist))
                    for j in range(steps):
                        t = j / steps
                        pos = pygame.Vector2(p1["pos"]).lerp(p2["pos"], t)
                        size = p1["size"] * (1 - t) + p2["size"] * t
                        color_t = (current_dist + dist * t) / path_length_pixels
                        color = utils.lerp_color(self.start_color, self.end_color, color_t)
                        elements_to_draw.append({"pos": pos, "color": color, "size": int(size), "type": "Circle"})
                    current_dist += dist

        elif self.brush_type == "Circle":
            if path_len >= 2 and path_length_pixels > 0:
                distance_covered = 0.0
                distance_since_last_stamp = 0.0
                for i in range(path_len - 1):
                    p1_data, p2_data = self.user_path[i], self.user_path[i + 1]
                    p1, p2 = pygame.Vector2(p1_data["pos"]), pygame.Vector2(p2_data["pos"])
                    segment_length = p1.distance_to(p2)
                    if segment_length == 0:
                        continue
                    dist_in_segment = 0.0
                    while dist_in_segment < segment_length:
                        current_t = dist_in_segment / segment_length
                        current_size = p1_data["size"] * (1 - current_t) + p2_data["size"] * current_t
                        spacing_pixels = max(1, current_size * (self.brush_spacing / 100.0))
                        if distance_since_last_stamp >= spacing_pixels:
                            stamp_pos = p1.lerp(p2, current_t)
                            path_t = (distance_covered + dist_in_segment) / path_length_pixels
                            jitter_amount = self.brush_color_jitter * (random.random() - 0.5)
                            final_t = max(0.0, min(1.0, path_t + jitter_amount))
                            color = utils.lerp_color(self.start_color, self.end_color, final_t)
                            elements_to_draw.append(
                                {"pos": stamp_pos, "color": color, "size": int(current_size), "type": "Circle"}
                            )
                            distance_since_last_stamp = 0
                        dist_in_segment += 1.0
                        distance_since_last_stamp += 1.0
                    distance_covered += segment_length

        elif self.brush_type == "Spray":
            for i, point_data in enumerate(self.user_path):
                center_pos = pygame.Vector2(point_data["pos"])
                brush_size = point_data["size"]
                num_dots = int(brush_size * 2)
                spray_radius = brush_size * 5
                color_t = i / (path_len - 1) if path_len > 1 else 0.5
                base_color = utils.lerp_color(self.start_color, self.end_color, color_t)
                for _ in range(num_dots):
                    random_angle = random.uniform(0, 360)
                    random_dist = abs(random.gauss(0, spray_radius / 3.0))
                    offset = pygame.Vector2(random_dist, 0).rotate(random_angle)
                    dot_size = random.uniform(max(1, 2 - self.brush_size_jitter), 2 + self.brush_size_jitter)
                    elements_to_draw.append(
                        {"pos": center_pos + offset, "color": base_color, "size": int(dot_size), "type": "Circle"}
                    )

        if elements_to_draw:
            action = AddPixelAction(
                self.layers[self.active_layer_index],
                elements_to_draw,
                self.num_slices,
                self.symmetry_mode,
            )
            self.history_manager.execute_action(action)

        self.is_drawing = False
        self.user_path.clear()
        self.spray_timer = 0.0

    def _action_start_export(self):
        filename = self.export_filename.strip() or "kaleido_art_" + datetime.datetime.now().strftime("%H%M%S")
        if self.export_format == "PNG":
            composite_image = drawing.get_composite_image(
                self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle
            )
            final_image = drawing.apply_global_dynamics(
                composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames
            )
            final_image = self._with_canvas_background(final_image)
            self.export_manager.start_png_export(filename, final_image)
        else:
            dynamics_params = {
                "enable_global_rotation": self.enable_global_rotation,
                "global_rotation_angle": self.global_rotation_angle,
                "enable_object_rotation": self.enable_object_rotation,
                "object_rotation_angle": self.object_rotation_angle,
                "enable_pulsing": self.enable_pulsing,
                "enable_trails": self.enable_trails,
                "rotation_cycles": 0.1,
                "background_color": self.canvas_color,
            }
            self.export_manager.start_gif_export(
                filename,
                self.layers,
                self.num_slices,
                self.symmetry_mode,
                dynamics_params,
                duration=3,
                rotation_cycles=0.1,
            )
        self.export_dialog_open = False
        self.export_text_active = False
