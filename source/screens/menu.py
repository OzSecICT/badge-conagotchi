"""Main navigation menu — sprite-based button system.

Each menu button lives at a fixed pixel position on the display.
Three image states per button:
  unselected  included in menu_bg.bin (no separate file needed)
  selected    img/btn_{id}_sel.bin   (w × h sprite)
  pressed     img/btn_{id}_press.bin (w × h sprite)

When the menu opens, menu_bg.bin is blitted (all buttons unselected), then
the first button's selected sprite is drawn on top.

Navigation (LEFT / RIGHT):
  1. Restore the old button's region from menu_bg.bin (row-seek, no large alloc).
  2. Blit the new button's selected sprite.

Activation (SELECT):
  1. Blit the pressed sprite immediately (synchronous).
  2. Set _pressing flag; update() waits _PRESS_MS then calls the target action.

──────────────────────────────────────────────────────────────────────────────
Button table  (_BUTTONS)
──────────────────────────────────────────────────────────────────────────────
Columns:  id | x | y | w | h | label

  id     — used to derive sprite filenames: img/btn_{id}_sel.bin etc.
  x, y   — top-left pixel of the button in the 240×240 display coordinate space.
           MUST match the position in your menu_bg.png artwork.
  w, h   — pixel dimensions of the button bounding box (and of the sprite files).
  label  — shown in the fallback primitive renderer when artwork is absent.

Update these values once you have finalised artwork.
──────────────────────────────────────────────────────────────────────────────
"""
import time
import gc9a01py as gc9a01
from screen_manager import Screen
from image_utils import blit_image, blit_sprite, restore_from_bg, draw_text
from buttons import LEFT, RIGHT, SELECT, START

# ── Button table ──────────────────────────────────────────────────────────────
# (id, x, y, w, h, label)
_B_ID    = 0
_B_X     = 1
_B_Y     = 2
_B_W     = 3
_B_H     = 4
_B_LABEL = 5

_BUTTONS = (
    #  id            x    y    w    h   label
    ("pet",          90,   5,  60,  45, "Pet"),    # top arc
    ("ctf",          30, 175,  60,  50, "CTF"),    # bottom arc, left
    ("settings",    150, 175,  60,  50, "Set"),    # bottom arc, right
)

_BG_PATH  = "img/menu_bg.bin"
_PRESS_MS = 150   # ms to hold pressed state before transitioning

# Fallback colours (primitive renderer, used when artwork files are absent)
_COL_BG    = gc9a01.color565( 20,  20,  30)
_COL_UNSEL = gc9a01.color565( 50,  50,  70)
_COL_SEL   = gc9a01.color565( 30,  80, 160)
_COL_PRESS = gc9a01.color565(220, 180,  40)


# ── Screen class ──────────────────────────────────────────────────────────────

class MainMenu(Screen):

    def __init__(self) -> None:
        self._sel      = 0
        self._pressing = False
        self._press_at = 0
        self._has_bg   = False

    async def enter(self, display, leds, mgr) -> None:
        self._pressing = False
        self._has_bg = _load_bg(display)
        _show_selected(display, self._sel, self._has_bg)

    async def update(self, display, leds, mgr) -> None:
        if self._pressing:
            if time.ticks_diff(time.ticks_ms(), self._press_at) >= _PRESS_MS:
                self._pressing = False
                _activate(self._sel, mgr)

    def handle_button(self, btn: str, mgr) -> None:
        if self._pressing:
            return

        if btn == LEFT:
            prev = self._sel
            self._sel = (self._sel - 1) % len(_BUTTONS)
            _deselect(mgr._display, prev, self._has_bg)
            _show_selected(mgr._display, self._sel, self._has_bg)

        elif btn == RIGHT:
            prev = self._sel
            self._sel = (self._sel + 1) % len(_BUTTONS)
            _deselect(mgr._display, prev, self._has_bg)
            _show_selected(mgr._display, self._sel, self._has_bg)

        elif btn in (SELECT, START):
            _show_pressed(mgr._display, self._sel, self._has_bg)
            self._pressing = True
            self._press_at = time.ticks_ms()


# ── Drawing ───────────────────────────────────────────────────────────────────

def _load_bg(display) -> bool:
    """Blit the background; return True if the image file existed."""
    try:
        blit_image(display, _BG_PATH)
        return True
    except OSError:
        display.fill(_COL_BG)
        for i in range(len(_BUTTONS)):
            _draw_btn_primitive(display, i, _COL_UNSEL)
        return False


def _show_selected(display, idx: int, has_bg: bool) -> None:
    b = _BUTTONS[idx]
    if not _try_sprite(display, f"img/btn_{b[_B_ID]}_sel.bin", b[_B_X], b[_B_Y], b[_B_W], b[_B_H]):
        _draw_btn_primitive(display, idx, _COL_SEL)


def _deselect(display, idx: int, has_bg: bool) -> None:
    b = _BUTTONS[idx]
    if has_bg:
        restore_from_bg(display, _BG_PATH, b[_B_X], b[_B_Y], b[_B_W], b[_B_H])
    else:
        _draw_btn_primitive(display, idx, _COL_UNSEL)


def _show_pressed(display, idx: int, has_bg: bool) -> None:
    b = _BUTTONS[idx]
    if not _try_sprite(display, f"img/btn_{b[_B_ID]}_press.bin", b[_B_X], b[_B_Y], b[_B_W], b[_B_H]):
        _draw_btn_primitive(display, idx, _COL_PRESS)


def _try_sprite(display, path: str, x: int, y: int, w: int, h: int) -> bool:
    """Blit a sprite; return True on success, False if the file is missing."""
    try:
        blit_sprite(display, path, x, y, w, h)
        return True
    except OSError:
        return False


def _draw_btn_primitive(display, idx: int, color: int) -> None:
    b = _BUTTONS[idx]
    display.fill_rect(b[_B_X], b[_B_Y], b[_B_W], b[_B_H], color)
    lx = b[_B_X] + (b[_B_W] - len(b[_B_LABEL]) * 8) // 2
    ly = b[_B_Y] + (b[_B_H] - 8) // 2
    draw_text(display, b[_B_LABEL], lx, ly, gc9a01.WHITE, color)


# ── Activation ────────────────────────────────────────────────────────────────

def _activate(idx: int, mgr) -> None:
    bid = _BUTTONS[idx][_B_ID]
    if bid == "pet":
        mgr.pop()
    elif bid == "ctf":
        pass  # TODO: from screens.challenges import ChallengeScreen; mgr.switch_to(ChallengeScreen())
    elif bid == "settings":
        pass  # TODO: from screens.settings import SettingsScreen; mgr.push(SettingsScreen())
