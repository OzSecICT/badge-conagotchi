"""
Image and text rendering helpers for the GC9A01 display.

Images are stored as raw big-endian RGB565 binary files (see tools/convert_image.py).

Full-screen files: 240 × 240 × 2 = 115,200 bytes.
Sprite files:      w × h × 2 bytes (no header — dimensions are known to the caller).

Text rendering piggybacks on MicroPython's framebuf built-in 8×8 font, with a
byte-swap to reconcile framebuf's little-endian storage with the driver's big-endian
SPI writes.
"""
import gc
import framebuf


_FULL_W = 240


def blit_image(display, path: str) -> None:
    """Stream a raw RGB565 .bin file to the full 240×240 display."""
    try:
        with open(path, "rb") as f:
            buf = f.read()
        display.blit_buffer(buf, 0, 0, _FULL_W, _FULL_W)
        del buf
    except MemoryError:
        # Row-at-a-time fallback if the heap is under pressure.
        with open(path, "rb") as f:
            row_buf = bytearray(_FULL_W * 2)
            for row in range(_FULL_W):
                n = f.readinto(row_buf)
                if not n:
                    break
                display.blit_buffer(row_buf, 0, row, _FULL_W, 1)
    gc.collect()


def blit_sprite(display, path: str, x: int, y: int, w: int, h: int) -> None:
    """
    Blit a small sprite from a raw RGB565 .bin file at position (x, y).

    The file must contain exactly w × h × 2 bytes — no header.
    Raises OSError if the file does not exist (caller can catch to use fallback).
    """
    with open(path, "rb") as f:
        buf = f.read()
    display.blit_buffer(buf, x, y, w, h)


def restore_from_bg(display, bg_path: str, x: int, y: int, w: int, h: int) -> None:
    """
    Re-blit a rectangular region from a full 240×240 background file.

    Seeks to each row's offset so only w×2 bytes are allocated at once — no need
    to load the full background into RAM.  Used to "undo" a sprite drawn over a bg.
    """
    row_buf = bytearray(w * 2)
    with open(bg_path, "rb") as f:
        for row in range(h):
            f.seek(((y + row) * _FULL_W + x) * 2)
            f.readinto(row_buf)
            display.blit_buffer(row_buf, x, y + row, w, 1)


def draw_text(display, text: str, x: int, y: int,
              fg: int = 0xFFFF, bg: int = 0x0000) -> None:
    """
    Draw a string using the framebuf built-in 8×8 pixel font.

    fg / bg are RGB565 big-endian values (same encoding as gc9a01py constants).
    Characters are 8 px wide × 8 px tall.
    """
    w = len(text) * 8
    if w <= 0:
        return
    buf = bytearray(w * 8 * 2)
    fb = framebuf.FrameBuffer(buf, w, 8, framebuf.RGB565)
    # framebuf uses little-endian storage; swap bytes so gc9a01 sees correct colours.
    fg_le = ((fg & 0xFF) << 8) | (fg >> 8)
    bg_le = ((bg & 0xFF) << 8) | (bg >> 8)
    fb.fill(bg_le)
    fb.text(text, 0, 0, fg_le)
    display.blit_buffer(bytes(buf), x, y, w, 8)
