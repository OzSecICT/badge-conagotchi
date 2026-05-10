"""Splash / boot logo screen.

Displays img/logo.bin if present; otherwise shows a colour-fill fallback.
Auto-advances to ConagotchiScreen after _AUTO_MS, or immediately on any button.
"""
import gc9a01py as gc9a01
from screen_manager import Screen
from image_utils import blit_image, draw_text
import time

_LOGO_PATH    = "img/logo.bin"
_AUTO_MS      = 3000
_BG_COLOR     = gc9a01.color565(10, 20, 40)   # dark navy fallback


class SplashScreen(Screen):

    async def enter(self, display, leds, mgr) -> None:
        self._start = time.ticks_ms()
        self._advanced = False
        try:
            blit_image(display, _LOGO_PATH)
        except OSError:
            _draw_fallback(display)

    async def update(self, display, leds, mgr) -> None:
        if not self._advanced and time.ticks_diff(time.ticks_ms(), self._start) >= _AUTO_MS:
            self._advance(mgr)

    def handle_button(self, btn: str, mgr) -> None:
        self._advance(mgr)

    def _advance(self, mgr) -> None:
        if self._advanced:
            return
        self._advanced = True
        from screens.conagotchi import ConagotchiScreen
        mgr.switch_to(ConagotchiScreen())


def _draw_fallback(display) -> None:
    display.fill(_BG_COLOR)
    # Centre "OzSec 2026" (10 chars × 8px = 80px wide) at x=80, y=105
    draw_text(display, "OzSec 2026",  80, 105, gc9a01.WHITE,  _BG_COLOR)
    draw_text(display, "Conagotchi",  80, 120, gc9a01.YELLOW, _BG_COLOR)
