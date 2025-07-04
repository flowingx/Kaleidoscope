# ui_handler.py
import pygame
import pygame_gui
from config import DRAW_AREA_WIDTH, UI_PANEL_WIDTH, LAYER_PANEL_WIDTH, SCREEN_HEIGHT

class UIHandler:
    def __init__(self, manager):
        self.manager = manager
        self.elements = {}
        self._setup_ui()

    def _create_divider(self, y_pos, container):
        """A helper function to create a visual divider."""
        divider = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(5, y_pos, UI_PANEL_WIDTH - 30, 2),
            manager=self.manager,
            container=container,
            object_id="@divider" # You can style this in theme.json if you want
        )
        return divider

    def _setup_ui(self):
        # Main Control Panel
        control_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((DRAW_AREA_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)),
            manager=self.manager)
        
        # --- Using a dynamic layout system ---
        y_pos = 10
        padding = 5  # Vertical space between elements
        label_height = 20
        element_height = 30
        section_padding = 15 # Space after a section divider

        # --- Section: Main Actions ---
        self.elements['generate_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, 40)), text='Generate New Layer', manager=self.manager, container=control_panel)
        y_pos += 40 + padding
        self.elements['clear_all_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, 30)), text='Clear All Drawings', manager=self.manager, container=control_panel)
        y_pos += 30 + section_padding
        self._create_divider(y_pos - (section_padding / 2), control_panel)
        
        # --- Section: Symmetry ---
        self.elements['symmetry_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, label_height)), text="Symmetry", manager=self.manager, container=control_panel)
        y_pos += label_height
        self.elements['kaleido_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, y_pos, 95, element_height)), text='Kaleido', manager=self.manager, container=control_panel)
        self.elements['rotate_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((115, y_pos, 95, element_height)), text='Rotate', manager=self.manager, container=control_panel)
        y_pos += element_height + padding
        
        self.elements['slice_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, 50, label_height)), text="Slices:", manager=self.manager, container=control_panel)
        self.elements['slice_input'] = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((60, y_pos, UI_PANEL_WIDTH - 90, element_height)), manager=self.manager, container=control_panel)
        y_pos += element_height + section_padding
        self._create_divider(y_pos - (section_padding / 2), control_panel)

        # --- Section: Brush ---
        self.elements['brush_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, label_height)), text="Brush", manager=self.manager, container=control_panel)
        y_pos += label_height
        self.elements['brush_dropdown'] = pygame_gui.elements.UIDropDownMenu(options_list=['Line', 'Circle', 'Spray'], starting_option='Line', relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, element_height)), manager=self.manager, container=control_panel)
        y_pos += element_height + padding
        self.elements['brush_size_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, label_height)), text="Size:", manager=self.manager, container=control_panel)
        y_pos += label_height
        self.elements['brush_size_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, 20)), start_value=5, value_range=(1, 15), manager=self.manager, container=control_panel)
        y_pos += 20 + section_padding
        self._create_divider(y_pos - (section_padding / 2), control_panel)

        # --- Section: Color ---
        self.elements['color_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, label_height)), text="Color Gradient", manager=self.manager, container=control_panel)
        y_pos += label_height + 40 # Extra space for the color boxes below
        
        # Note: Color boxes and spectrum are drawn manually in app.py, 
        # so we just need to reserve space for them here in our layout calculation.
        y_pos += 50 # Space for color boxes
        y_pos += 150 # Space for spectrum
        y_pos += section_padding
        self._create_divider(y_pos - (section_padding / 2), control_panel)
        
        # --- Section: Effects & Export ---
        self.elements['dynamics_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, label_height)), text="Dynamic Effects", manager=self.manager, container=control_panel)
        y_pos += label_height
        self.elements['rotate_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, y_pos, 95, element_height)), text='Rotate', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        self.elements['pulse_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((115, y_pos, 95, element_height)), text='Pulse', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        y_pos += element_height + padding * 3
        
        self.elements['export_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, y_pos, UI_PANEL_WIDTH - 40, 40)), text='Export...', manager=self.manager, container=control_panel)


        # --- Layer Panel ---
        layer_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((DRAW_AREA_WIDTH + UI_PANEL_WIDTH, 0, LAYER_PANEL_WIDTH, SCREEN_HEIGHT)),
            manager=self.manager)
        self.elements['layer_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 5, LAYER_PANEL_WIDTH, 20)), text="Layers", manager=self.manager, container=layer_panel, object_id="@centered_label")
        self.elements['layer_list'] = pygame_gui.elements.UISelectionList(relative_rect=pygame.Rect((10, 30, 160, SCREEN_HEIGHT - 80)), item_list=[], manager=self.manager, container=layer_panel)
        self.elements['delete_layer_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, SCREEN_HEIGHT - 45, 160, 30)), text='Delete Selected', manager=self.manager, container=layer_panel)