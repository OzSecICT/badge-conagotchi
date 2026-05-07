# menu.py
import gc9a01py as gc9a01

class Menu:
    def __init__(self, tft, items, background_color=gc9a01.BLACK):
        self.tft = tft
        self.items = items
        self.selected_index = 0
        self.background_color = background_color
        
        # Display constants for 240x240 round screen
        self.width = 240
        self.height = 240
        self.center_x = 120
        self.center_y = 120
        self.radius = 120

    def draw(self):
        # We'll use a circular menu system: 
        # items are placed around the top and bottom of the display.
        
        # Draw background or clear menu area
        # For simplicity, let's just draw the items at specific positions.
        
        # Number of items to display (subset of total items)
        num_visible = 3
        
        # Position mapping: (item_index, x, y, is_selected)
        # Top area (item before selected)
        prev_idx = (self.selected_index - 1) % len(self.items)
        # 120, 30 is roughly top of the circle
        self._draw_item(self.items[prev_idx], 120, 30, False)
        
        # Center area (selected item)
        self._draw_item(self.items[self.selected_index], 120, 120, True)
        
        # Bottom area (item after selected)
        next_idx = (self.selected_index + 1) % len(self.items)
        # 120, 210 is roughly bottom of the circle
        self._draw_item(self.items[next_idx], 120, 210, False)

    def _draw_item(self, text, x, y, selected):
        color = gc9a01.YELLOW if selected else gc9a01.WHITE
        # Simple centering based on 8x8 font
        # If tft.font is not available, this might fail. 
        # Based on hwtest.py, tft.font seems to be expected.
        try:
            font = self.tft.font
            width = len(text) * 8 # assuming 8x8 font
            self.tft.text(font, text, x - (width // 2), y, color, self.background_color)
        except AttributeError:
            # Fallback if font is not set on tft
            pass

    def next(self):
        self.selected_index = (self.selected_index + 1) % len(self.items)
        self.draw()

    def prev(self):
        self.selected_index = (self.selected_index - 1) % len(self.items)
        self.draw()

    def get_selected(self):
        return self.items[self.selected_index]
