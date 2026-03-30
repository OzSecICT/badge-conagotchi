# hwtest.py
# OzSec 2026 Conagotchi — hardware verification test
# Tests: display, all buttons, alert LED, raffle LED, RGB strip
# Flash this alone. No other project files needed.

import machine
import time
import neopixel
import gc9a01py as gc9a01
import config

# ── Colors (RGB565) ──────────────────────────────────────
BLACK  = 0x0000
WHITE  = 0xFFFF
RED    = 0xF800
GREEN  = 0x07E0
BLUE   = 0x001F
YELLOW = 0xFFE0
CYAN   = 0x07FF

# ── Hardware init ────────────────────────────────────────

def init_display():
    spi = machine.SPI(1,
                      baudrate=40_000_000,
                      sck=machine.Pin(config.PIN_DISPLAY_SCK),
                      mosi=machine.Pin(config.PIN_DISPLAY_MOSI))
    tft = gc9a01.GC9A01(spi,
                        dc=machine.Pin(config.PIN_DISPLAY_DC),
                        cs=machine.Pin(config.PIN_DISPLAY_CS),
                        reset=machine.Pin(config.PIN_DISPLAY_RST),
                        rotation=0)
    tft.init()
    return tft

def init_buttons():
    return {
        "BOOT":   machine.Pin(config.PIN_BTN_BOOT,   machine.Pin.IN, machine.Pin.PULL_UP),
        "START":  machine.Pin(config.PIN_BTN_START,  machine.Pin.IN, machine.Pin.PULL_UP),
        "SELECT": machine.Pin(config.PIN_BTN_SELECT, machine.Pin.IN, machine.Pin.PULL_UP),
        "RIGHT":  machine.Pin(config.PIN_BTN_RIGHT,  machine.Pin.IN, machine.Pin.PULL_UP),
        "LEFT":   machine.Pin(config.PIN_BTN_LEFT,   machine.Pin.IN, machine.Pin.PULL_UP),
    }

def init_leds():
    alert  = machine.Pin(config.PIN_LED_ALERT,  machine.Pin.OUT)
    raffle = machine.Pin(config.PIN_LED_RAFFLE, machine.Pin.OUT)
    rgb    = neopixel.NeoPixel(machine.Pin(config.PIN_LED_RGB), config.NUM_RGB_LEDS)
    alert.value(0)
    raffle.value(0)
    for i in range(config.NUM_RGB_LEDS):
        rgb[i] = (0, 0, 0)
    rgb.write()
    return alert, raffle, rgb

# ── Display helpers ──────────────────────────────────────

def draw_status(tft, buttons, alert_on, raffle_on, rgb_mode):
    tft.fill(BLACK)

    # Title
    tft.text(tft.font, "HW TEST", 70, 10, WHITE, BLACK)

    # Button states — one row each
    y = 40
    for name, pin in buttons.items():
        pressed = pin.value() == 0   # active low
        color   = GREEN if pressed else WHITE
        state   = "DOWN" if pressed else "    "
        tft.text(tft.font, f"{name:<6} {state}", 20, y, color, BLACK)
        y += 20

    # LED states
    tft.text(tft.font, "─" * 18, 10, y + 5, CYAN, BLACK)
    y += 20
    tft.text(tft.font, f"ALERT:  {'ON ' if alert_on  else 'OFF'}", 20, y,      YELLOW if alert_on  else WHITE, BLACK)
    tft.text(tft.font, f"RAFFLE: {'ON ' if raffle_on else 'OFF'}", 20, y + 20, YELLOW if raffle_on else WHITE, BLACK)

    # RGB mode
    RGB_LABELS = ["OFF", "RED", "GREEN", "BLUE", "WHITE", "CYCLE"]
    tft.text(tft.font, f"RGB:    {RGB_LABELS[rgb_mode]}", 20, y + 40, CYAN, BLACK)

    # Controls hint at bottom
    tft.text(tft.font, "L/R:RGB  ST:ALT  SE:RAF", 5, 210, CYAN, BLACK)

def set_rgb_mode(rgb, mode):
    COLORS = [
        (0,   0,   0  ),   # 0 off
        (255, 0,   0  ),   # 1 red
        (0,   255, 0  ),   # 2 green
        (0,   0,   255),   # 3 blue
        (255, 255, 255),   # 4 white
    ]
    if mode < len(COLORS):
        for i in range(config.NUM_RGB_LEDS):
            rgb[i] = COLORS[mode]
        rgb.write()
    # mode 5 (CYCLE) is handled in the loop

# ── Button edge detection ─────────────────────────────────

class EdgeDetector:
    """Tracks previous pin state to detect press events (not held)."""
    def __init__(self, buttons):
        self._prev = {name: 1 for name in buttons}

    def get_events(self, buttons):
        events = []
        for name, pin in buttons.items():
            val = pin.value()
            if val == 0 and self._prev[name] == 1:
                events.append(name)
            self._prev[name] = val
        return events

# ── Main loop ────────────────────────────────────────────

def main():
    print("Conagotchi HW Test starting...")

    tft     = init_display()
    buttons = init_buttons()
    alert, raffle, rgb = init_leds()
    edges   = EdgeDetector(buttons)

    alert_on  = False
    raffle_on = False
    rgb_mode  = 0   # 0=off, 1=red, 2=green, 3=blue, 4=white, 5=cycle
    cycle_hue = 0

    tft.fill(BLACK)
    tft.text(tft.font, "Initializing...", 40, 110, WHITE, BLACK)
    time.sleep_ms(500)

    while True:
        events = edges.get_events(buttons)

        for event in events:
            print(f"Button: {event}")   # also log to serial for debugging

            if event == "START":
                alert_on = not alert_on
                alert.value(1 if alert_on else 0)

            elif event == "SELECT":
                raffle_on = not raffle_on
                raffle.value(1 if raffle_on else 0)

            elif event == "RIGHT":
                rgb_mode = (rgb_mode + 1) % 6
                if rgb_mode < 5:
                    set_rgb_mode(rgb, rgb_mode)

            elif event == "LEFT":
                rgb_mode = (rgb_mode - 1) % 6
                if rgb_mode < 5:
                    set_rgb_mode(rgb, rgb_mode)

        # RGB cycle mode
        if rgb_mode == 5:
            for i in range(config.NUM_RGB_LEDS):
                hue = (cycle_hue + i * 30) % 360
                rgb[i] = _hsv_to_rgb(hue, 255, 128)
            rgb.write()
            cycle_hue = (cycle_hue + 5) % 360

        draw_status(tft, buttons, alert_on, raffle_on, rgb_mode)
        time.sleep_ms(50)

def _hsv_to_rgb(h, s, v):
    """Minimal HSV to RGB for the cycle animation. h=0-359, s/v=0-255."""
    h = h % 360
    i = h // 60
    f = (h % 60) * 255 // 60
    p = v * (255 - s) // 255
    q = v * (255 - s * f // 255) // 255
    t = v * (255 - s * (255 - f) // 255) // 255
    return [
        (v, t, p), (q, v, p), (p, v, t),
        (p, q, v), (t, p, v), (v, p, q)
    ][i]

main()