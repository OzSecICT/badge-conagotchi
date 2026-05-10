"""Main Conagotchi idle / pet screen.

Layout (240×240 round display, centre 120,120, radius 120)
───────────────────────────────────────────────────────────
  Background   img/bg_main.bin  (full 240×240) or solid colour fallback
  Character    img/char_idle_N.bin sprites inside _CHAR bounding box
  Stat bars    bottom arc, y ≈ 183–200

Character animation
───────────────────
  Supply 4–8 frame PNGs named  img/char_idle_0.bin … img/char_idle_N.bin.
  See CLAUDE.md "Image workflow" for the conversion command.
  The animation runs in pingpong mode at _ANIM_MS ms per frame.

  When sprite files are absent a primitive fallback animates:
    frames 0–2  breathing bob (character shifts down 0 / 2 / 3 px)
    frame  3    blink (eyes closed) + bob at 2 px
    every _BLINK_EVERY ticks  an extra blink regardless of frame

TODO: real pet state model
TODO: action menu on START (feed / drink / play / sleep)
"""
import time
import gc9a01py as gc9a01
from screen_manager import Screen
from image_utils import blit_image, draw_text
from anim import SpriteAnim
from buttons import SELECT, START, LEFT, RIGHT

# ── Active character ──────────────────────────────────────────────────────────
# Folder name under img/ for the active character's assets.
# Each character folder contains: background.bin, character.bin (idle frame 0),
# and optionally idle_1.bin … idle_N.bin for additional animation frames.
_CHARACTER = "hackachi"

_BG_PATH = f"img/{_CHARACTER}/background.bin"

_IDLE_FRAMES = [
    f"img/{_CHARACTER}/character.bin",
    # Add  img/{_CHARACTER}/idle_1.bin  etc. as more frames are created
]

# ── Character bounding box ────────────────────────────────────────────────────
# character.bin is 80×80 px.  Centred horizontally; feet sit just above stats.
_CHAR_X = 80    # (240 - 80) // 2
_CHAR_Y = 98    # bottom of sprite at y=178, 5 px above stat labels at y=183
_CHAR_W = 80
_CHAR_H = 80

_ANIM_MS      = 300   # ms per animation frame
_BLINK_EVERY  = 10    # insert an extra blink every N ticks (~3 s at 300 ms/frame)

# ── Stat bar geometry ─────────────────────────────────────────────────────────
_BAR_LABEL_Y = 183
_BAR_Y       = 192
_BAR_H       = 8
_BAR_W       = 40
_BAR_GAP     = 12
_BAR_X0      = 40

# ── Colours ───────────────────────────────────────────────────────────────────
_BG_COLOR    = gc9a01.color565( 15,  35,  25)
_COL_HUNGER  = gc9a01.color565(220,  80,  40)
_COL_THIRST  = gc9a01.color565( 40, 120, 220)
_COL_HAPPY   = gc9a01.color565(220, 190,  40)
_COL_ENERGY  = gc9a01.color565( 60, 200,  80)
_COL_BAR_BG  = gc9a01.color565( 40,  40,  40)

# Primitive character colours (used when sprite files are absent)
_COL_BODY    = gc9a01.color565(230, 210, 175)
_COL_EYE     = gc9a01.color565( 40,  30,  50)
_COL_SHINE   = gc9a01.WHITE
_COL_SMILE   = gc9a01.color565(190,  80,  80)
_COL_CHEEK   = gc9a01.color565(230, 150, 150)


class ConagotchiScreen(Screen):

    def __init__(self) -> None:
        # Placeholder pet state — replace with a real model later
        self.hunger    = 60
        self.thirst    = 40
        self.happiness = 75
        self.energy    = 80

        self._has_bg   = False
        self._anim     = SpriteAnim(
            _IDLE_FRAMES,
            x=_CHAR_X, y=_CHAR_Y, w=_CHAR_W, h=_CHAR_H,
            ms_per_frame=_ANIM_MS,
            mode="pingpong",
        )

    async def enter(self, display, leds, mgr) -> None:
        self._has_bg = _load_bg(display)
        self._anim.reset()
        self._anim.draw_current(display, _BG_PATH if self._has_bg else None)
        if not self._anim.has_sprites:
            _draw_char_primitive(display, _CHAR_X, _CHAR_Y, frame=0, blink=False)
        self._draw_stats(display)

    async def update(self, display, leds, mgr) -> None:
        now = time.ticks_ms()
        bg  = _BG_PATH if self._has_bg else None

        if self._anim.tick(display, bg, now):
            if not self._anim.has_sprites:
                # Determine whether this tick is a blink frame
                f  = self._anim.frame_idx
                tc = self._anim.tick_count
                blink = (f == 3) or (tc % _BLINK_EVERY == 0)
                # Clear char region (no bg file — fill with solid colour)
                if not self._has_bg:
                    display.fill_rect(_CHAR_X, _CHAR_Y, _CHAR_W, _CHAR_H, _BG_COLOR)
                _draw_char_primitive(display, _CHAR_X, _CHAR_Y, f, blink)

    def handle_button(self, btn: str, mgr) -> None:
        if btn == SELECT:
            from screens.menu import MainMenu
            mgr.push(MainMenu())
        elif btn == START:
            pass  # TODO: push action menu (feed / drink / play / sleep)
        elif btn == LEFT:
            pass  # TODO: cycle status view
        elif btn == RIGHT:
            pass  # TODO: cycle status view

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_stats(self, display) -> None:
        stats = [
            ("H", self.hunger,    _COL_HUNGER),
            ("T", self.thirst,    _COL_THIRST),
            ("J", self.happiness, _COL_HAPPY),
            ("E", self.energy,    _COL_ENERGY),
        ]
        for i, (label, value, color) in enumerate(stats):
            x = _BAR_X0 + i * (_BAR_W + _BAR_GAP)
            draw_text(display, label, x, _BAR_LABEL_Y, gc9a01.WHITE, _BG_COLOR)
            display.fill_rect(x, _BAR_Y, _BAR_W, _BAR_H, _COL_BAR_BG)
            filled = int(_BAR_W * value / 100)
            if filled > 0:
                display.fill_rect(x, _BAR_Y, filled, _BAR_H, color)


# ── Module-level helpers ──────────────────────────────────────────────────────

def _load_bg(display) -> bool:
    try:
        blit_image(display, _BG_PATH)
        return True
    except OSError:
        display.fill(_BG_COLOR)
        return False


# Breathing bob: y offset (px) for frames 0-3
_BOB = (0, 1, 2, 1)


def _draw_char_primitive(display, bx: int, by: int, frame: int, blink: bool) -> None:
    """Fallback character drawn with fill_rects when sprite files are absent.
    Fits within the 80×80 bounding box.  frame 0-3: breathing bob.  blink: eyes closed."""
    bob = _BOB[frame % 4]
    ox  = bx
    oy  = by + bob

    # Body (egg shape)
    display.fill_rect(ox + 22, oy +  6, 36, 56, _COL_BODY)
    display.fill_rect(ox + 16, oy + 14, 48, 40, _COL_BODY)
    display.fill_rect(ox + 19, oy +  9, 42, 50, _COL_BODY)

    # Eyes
    eye_y = oy + 20
    if blink:
        display.fill_rect(ox + 22, eye_y + 4, 12, 3, _COL_EYE)
        display.fill_rect(ox + 46, eye_y + 4, 12, 3, _COL_EYE)
    else:
        display.fill_rect(ox + 22, eye_y,     12, 11, _COL_EYE)
        display.fill_rect(ox + 46, eye_y,     12, 11, _COL_EYE)
        display.fill_rect(ox + 24, eye_y + 2,  4,  4, _COL_SHINE)
        display.fill_rect(ox + 48, eye_y + 2,  4,  4, _COL_SHINE)

    # Cheeks
    display.fill_rect(ox + 14, oy + 33, 10, 5, _COL_CHEEK)
    display.fill_rect(ox + 56, oy + 33, 10, 5, _COL_CHEEK)

    # Smile
    display.fill_rect(ox + 26, oy + 40,  3, 3, _COL_SMILE)
    display.fill_rect(ox + 29, oy + 42, 10, 3, _COL_SMILE)
    display.fill_rect(ox + 39, oy + 40,  3, 3, _COL_SMILE)

    # Feet
    display.fill_rect(ox + 20, oy + 60, 16, 10, _COL_BODY)
    display.fill_rect(ox + 44, oy + 60, 16, 10, _COL_BODY)
