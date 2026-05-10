"""
Sprite-based animation helper for the GC9A01 display.

Usage
─────
  anim = SpriteAnim(
      frames       = ["img/idle_0.bin", "img/idle_1.bin", "img/idle_2.bin"],
      x=70, y=52, w=100, h=115,
      ms_per_frame = 300,
      mode         = "pingpong",   # or "loop"
  )

  # In enter() / resume():
  anim.draw_current(display, bg_path)

  # In update():
  if anim.tick(display, bg_path, time.ticks_ms()):
      if not anim.has_sprites:
          # draw your primitive fallback here, using anim.frame_idx
          pass

Frame files are raw big-endian RGB565 binaries sized to w×h (see tools/convert_image.py).
bg_path is the full 240×240 background file used to erase the previous frame before
drawing the next one.  Pass None if no background file exists.
"""
import time
from image_utils import blit_sprite, restore_from_bg


class SpriteAnim:
    """Cycles through a list of sprite files at a fixed frame rate."""

    def __init__(self, frames, x: int, y: int, w: int, h: int,
                 ms_per_frame: int = 300, mode: str = "pingpong",
                 pre_composited: bool = True) -> None:
        self._frames = frames
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._ms              = ms_per_frame
        self._mode            = mode
        self._pre_composited  = pre_composited  # sprites already contain bg pixels
        self._idx             = 0
        self._dir             = 1
        self._last_ms         = 0
        self.frame_idx        = 0   # current frame index (read-only for callers)
        self.tick_count       = 0   # total frames advanced since reset
        self.has_sprites      = False   # True after first successful sprite blit

    # ── Public API ────────────────────────────────────────────────────────────

    def draw_current(self, display, bg_path: str = None) -> None:
        """Draw the current frame immediately (call from enter / resume)."""
        self._draw(display, bg_path)

    def tick(self, display, bg_path: str = None, now: int = None) -> bool:
        """
        Advance and draw if the frame interval has elapsed.

        Returns True if the frame advanced (caller should draw fallback if
        not has_sprites).  bg_path is the full-screen background file used
        to restore the sprite region before drawing the next frame; pass None
        if only a solid-colour fallback is available.
        """
        if now is None:
            now = time.ticks_ms()
        if time.ticks_diff(now, self._last_ms) < self._ms:
            return False
        self._last_ms = now
        self._advance()
        self._draw(display, bg_path)
        return True

    def reset(self) -> None:
        """Return to frame 0 and clear the tick counter."""
        self._idx       = 0
        self._dir       = 1
        self.frame_idx  = 0
        self.tick_count = 0
        self._last_ms   = 0

    # ── Internal ──────────────────────────────────────────────────────────────

    def _advance(self) -> None:
        n = len(self._frames)
        if n <= 1:
            self.tick_count += 1
            return
        if self._mode == "loop":
            self._idx = (self._idx + 1) % n
        else:  # pingpong
            self._idx += self._dir
            if self._idx >= n - 1:
                self._dir = -1
            elif self._idx <= 0:
                self._dir = 1
        self.frame_idx  = self._idx
        self.tick_count += 1

    def _draw(self, display, bg_path: str) -> None:
        if self._pre_composited:
            # Sprite already contains the background pixels — blit directly.
            # This avoids the restore→blit flash caused by briefly showing a
            # bare background between frames.  Only restore if the sprite file
            # is missing so the primitive fallback has a clean surface to draw on.
            try:
                blit_sprite(display, self._frames[self._idx],
                            self.x, self.y, self.w, self.h)
                self.has_sprites = True
                return
            except OSError:
                self.has_sprites = False
        else:
            # Non-pre-composited sprites need the background restored first.
            if bg_path is not None:
                try:
                    restore_from_bg(display, bg_path, self.x, self.y, self.w, self.h)
                except OSError:
                    pass
            try:
                blit_sprite(display, self._frames[self._idx],
                            self.x, self.y, self.w, self.h)
                self.has_sprites = True
                return
            except OSError:
                self.has_sprites = False

        # Sprite missing — restore background so the primitive fallback has a
        # clean surface (the caller draws the primitive after this returns).
        if bg_path is not None:
            try:
                restore_from_bg(display, bg_path, self.x, self.y, self.w, self.h)
            except OSError:
                pass
