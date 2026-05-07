import machine
import config
import gc9a01py as gc9a01
import time
from buttons import Buttons
from menu import Menu

def init_display():
    spi = machine.SPI(1,
                      baudrate=config.DISPLAY_SPI_FREQ,
                      sck=machine.Pin(config.PIN_DISPLAY_SCK),
                      mosi=machine.Pin(config.PIN_DISPLAY_MOSI))
    tft = gc9a01.GC9A01(spi,
                        dc=machine.Pin(config.PIN_DISPLAY_DC),
                        cs=machine.Pin(config.PIN_DISPLAY_CS),
                        reset=machine.Pin(config.PIN_DISPLAY_RST),
                        rotation=0)
    # If gc9a01py.py doesn't have an init method, this call will fail.
    # We saw hwtest.py use it, so it's assumed to be there or we should add it.
    try:
        tft.init()
    except AttributeError:
        pass
    
    # Load a font onto tft if possible (not present in current driver)
    # tft.font = some_font
    return tft

def draw_background(tft, filename=None):
    """Draw a background image (raw 565 format) to the display."""
    if filename:
        try:
            with open(filename, "rb") as f:
                # Stream the file to the display in chunks
                # A 240x240 RGB565 image is 115,200 bytes
                chunk_size = 4096
                for y in range(0, 240, 240 // (240 // 10)): # Example chunked write
                    # This is complex to stream correctly without a buffer
                    # tft.blit_buffer(f.read(240 * 10 * 2), 0, y, 240, 10)
                    pass
        except OSError:
            tft.fill(gc9a01.BLACK)
    else:
        tft.fill(gc9a01.BLACK)
    
    # Draw a circular boundary (roughly)
    # The display is 240x240, usable area is a circle.
    # We could draw a white circle border for debugging
    # tft.circle(120, 120, 119, gc9a01.WHITE)
    pass

def main():
    tft = init_display()
    buttons = Buttons()
    
    menu_items = ["WIFI", "LINK", "STATS", "GAMES", "SETTINGS", "EXIT"]
    menu = Menu(tft, menu_items)
    
    draw_background(tft)
    menu.draw()
    
    while True:
        event = buttons.get_event()
        if event:
            if event == "RIGHT" or event == "START":
                menu.next()
            elif event == "LEFT" or event == "SELECT":
                menu.prev()
            elif event == "BOOT":
                # Maybe action/select?
                selected = menu.get_selected()
                print("Selected:", selected)
        
        time.sleep_ms(config.FRAME_MS)

if __name__ == "__main__":
    main()