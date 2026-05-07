from machine import Pin
import time
from config import PIN_BTN_BOOT, PIN_BTN_START, PIN_BTN_SELECT, PIN_BTN_RIGHT, PIN_BTN_LEFT, DEBOUNCE_MS

class Buttons:
    def __init__(self):
        self.pins = {
            "BOOT": Pin(PIN_BTN_BOOT, Pin.IN, Pin.PULL_UP),
            "START": Pin(PIN_BTN_START, Pin.IN, Pin.PULL_UP),
            "SELECT": Pin(PIN_BTN_SELECT, Pin.IN, Pin.PULL_UP),
            "RIGHT": Pin(PIN_BTN_RIGHT, Pin.IN, Pin.PULL_UP),
            "LEFT": Pin(PIN_BTN_LEFT, Pin.IN, Pin.PULL_UP),
        }
        self.last_press = {name: 0 for name in self.pins}
        self.events = []

        for name, pin in self.pins.items():
            pin.irq(trigger=Pin.IRQ_FALLING, handler=lambda p, n=name: self._handler(n))

    def _handler(self, name):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_press[name]) > DEBOUNCE_MS:
            self.events.append(name)
            self.last_press[name] = now

    def get_event(self):
        if self.events:
            return self.events.pop(0)
        return None