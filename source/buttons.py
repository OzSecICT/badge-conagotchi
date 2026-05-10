import asyncio
from machine import Pin
import time
from config import (
    PIN_BTN_BOOT, PIN_BTN_START, PIN_BTN_SELECT,
    PIN_BTN_RIGHT, PIN_BTN_LEFT, DEBOUNCE_MS,
)

BOOT   = "BOOT"
START  = "START"
SELECT = "SELECT"
RIGHT  = "RIGHT"
LEFT   = "LEFT"

_PINS = {
    BOOT:   PIN_BTN_BOOT,
    START:  PIN_BTN_START,
    SELECT: PIN_BTN_SELECT,
    RIGHT:  PIN_BTN_RIGHT,
    LEFT:   PIN_BTN_LEFT,
}

_BUF_MAX = 8


class Buttons:
    def __init__(self):
        self._pins = {
            name: Pin(pin, Pin.IN, Pin.PULL_UP)
            for name, pin in _PINS.items()
        }
        self._last_ms = {name: 0 for name in _PINS}
        self._buf = []

        for name, pin in self._pins.items():
            pin.irq(
                trigger=Pin.IRQ_FALLING,
                handler=lambda p, n=name: self._isr(n),
            )

    def _isr(self, name):
        now = time.ticks_ms()
        if self._pins[name].value() != 0:
            return  # ignore rising edge entirely — only falling edges count
        last = self._last_ms[name]
        self._last_ms[name] = now  # update timer on every falling edge (not rising)
        if time.ticks_diff(now, last) >= DEBOUNCE_MS:
            if len(self._buf) < _BUF_MAX:
                self._buf.append(name)

    def clear(self) -> None:
        """Discard all queued events. Call after screen transitions to prevent
        the triggering press from being re-delivered to the incoming screen."""
        self._buf.clear()

    async def get(self):
        """Wait for and return the next button name."""
        while not self._buf:
            await asyncio.sleep_ms(10)
        return self._buf.pop(0)

    def pressed(self, name):
        """Return True if the button is currently held down."""
        return self._pins[name].value() == 0
