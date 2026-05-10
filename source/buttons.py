import asyncio
from asyncio import Queue
from machine import Pin
import time
from config import (
    PIN_BTN_BOOT, PIN_BTN_START, PIN_BTN_SELECT,
    PIN_BTN_RIGHT, PIN_BTN_LEFT, DEBOUNCE_MS,
)

# Named constants so callers use Buttons.START rather than string literals.
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


class Buttons:
    def __init__(self):
        self._pins = {
            name: Pin(pin, Pin.IN, Pin.PULL_UP)
            for name, pin in _PINS.items()
        }
        self._last_ms = {name: 0 for name in _PINS}
        self._queue   = Queue()

        for name, pin in self._pins.items():
            pin.irq(
                trigger=Pin.IRQ_FALLING,
                handler=lambda p, n=name: self._isr(n),
            )

    def _isr(self, name):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_ms[name]) >= DEBOUNCE_MS:
            self._last_ms[name] = now
            try:
                self._queue.put_nowait(name)
            except Exception:
                pass  # queue full — drop the event

    async def get(self):
        """Wait for and return the next button name."""
        return await self._queue.get()

    def pressed(self, name):
        """Return True if the button is currently held down."""
        return self._pins[name].value() == 0
