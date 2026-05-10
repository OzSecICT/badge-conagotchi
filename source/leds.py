from machine import Pin
from neopixel import NeoPixel
from config import PIN_LED_ALERT, PIN_LED_RAFFLE, PIN_LED_RGB, NUM_RGB_LEDS


class Leds:
    def __init__(self):
        self.alert  = Pin(PIN_LED_ALERT,  Pin.OUT, value=0)
        self.raffle = Pin(PIN_LED_RAFFLE, Pin.OUT, value=0)
        self.rgb    = NeoPixel(Pin(PIN_LED_RGB, Pin.OUT), NUM_RGB_LEDS)
        self.rgb_off()

    # ── Alert / Raffle ─────────────────────────────────────────────────────

    def set_alert(self, on: bool):
        self.alert(1 if on else 0)

    def set_raffle(self, on: bool):
        self.raffle(1 if on else 0)

    # ── WS2812B helpers ────────────────────────────────────────────────────

    def rgb_set(self, idx: int, r: int, g: int, b: int):
        self.rgb[idx] = (r, g, b)

    def rgb_fill(self, r: int, g: int, b: int):
        for i in range(NUM_RGB_LEDS):
            self.rgb[i] = (r, g, b)

    def rgb_off(self):
        self.rgb_fill(0, 0, 0)
        self.rgb.write()

    def rgb_show(self):
        self.rgb.write()

    def all_off(self):
        self.set_alert(False)
        self.set_raffle(False)
        self.rgb_off()
