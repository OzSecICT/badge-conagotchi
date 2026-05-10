#!/usr/bin/env python3
"""
Convert PNG images to raw big-endian RGB565 binary files for the GC9A01 display.

The driver (gc9a01py) expects big-endian RGB565 pixels written directly over SPI.

Requirements:
    pip install Pillow

──────────────────────────────────────────────────────────────────────────────
Full-screen images  (240 × 240, e.g. backgrounds)
──────────────────────────────────────────────────────────────────────────────
    python tools/convert_image.py assets/logo.png --outdir source/img

    # Composite an RGBA overlay onto a background (pre-flatten transparency):
    python tools/convert_image.py bg.png overlay.png --composite --output source/img/menu_bg.bin

──────────────────────────────────────────────────────────────────────────────
Sprites with transparency  (characters, buttons, etc.)
──────────────────────────────────────────────────────────────────────────────
RGB565 has no alpha channel, so transparent pixels must be resolved at
conversion time by compositing the sprite onto the background it will
appear on.  Use --on-bg with --pos to specify the background and the
sprite's top-left position within it:

    python tools/convert_image.py character.png \\
        --no-resize \\
        --on-bg assets/hackachi/Hackachi-BG_V2.png --pos 80,98 \\
        --output source/img/hackachi/character.bin

    # x,y in --pos must match _CHAR_X, _CHAR_Y in source/screens/conagotchi.py

──────────────────────────────────────────────────────────────────────────────
Button sprites  (small files sized to the button bounding box)
──────────────────────────────────────────────────────────────────────────────
Option A — provide a pre-sized PNG for each button state:
    python tools/convert_image.py btn_pet_sel.png --no-resize --outdir source/img

Option B — design in full 240×240 mockups and crop out each button region:
    python tools/convert_image.py menu_pet_sel.png --crop 90,5,60,45 \\
        --output source/img/btn_pet_sel.bin

    Crop format:  x,y,w,h  (top-left origin, matches _BUTTONS table in menu.py)

──────────────────────────────────────────────────────────────────────────────
"""

import sys
import struct
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required:  pip install Pillow")
    sys.exit(1)

_DEFAULT_W, _DEFAULT_H = 240, 240


def _to_rgb565(img: Image.Image) -> bytes:
    """Return big-endian RGB565 bytes for a PIL Image (must already be correct size)."""
    img = img.convert("RGB")
    w, h = img.size
    raw = img.tobytes()          # packed [R,G,B, R,G,B, …]
    buf = bytearray(w * h * 2)
    for i in range(w * h):
        r, g, b = raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]
        color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        struct.pack_into(">H", buf, i * 2, color)
    return bytes(buf)


def _open_and_prepare(src: Path, size=None, crop=None, no_resize=False,
                      on_bg: Path = None, pos=None) -> Image.Image:
    """
    Open src and apply crop / resize / background-composite to produce the final image.

    crop     — (x, y, w, h) crops from the source image
    size     — (w, h) resize target
    no_resize — use source pixels as-is (after optional crop)
    on_bg    — background image to composite the sprite onto (resolves transparency)
    pos      — (x, y) top-left position of the sprite within the background
    """
    img = Image.open(src)

    if crop is not None:
        cx, cy, cw, ch = crop
        img = img.crop((cx, cy, cx + cw, cy + ch))
        # Crop already gives the right size — skip further resize.
    elif not no_resize:
        target = size or (_DEFAULT_W, _DEFAULT_H)
        if img.size != target:
            img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
            img = img.resize(target, Image.LANCZOS)

    if on_bg is not None:
        # Composite the sprite onto the relevant region of the background so
        # transparent pixels show the background rather than converting to black.
        if pos is None:
            raise ValueError("--on-bg requires --pos x,y")
        x, y = pos
        w, h = img.size
        bg = Image.open(on_bg).convert("RGBA")
        if bg.size != (_DEFAULT_W, _DEFAULT_H):
            bg = bg.resize((_DEFAULT_W, _DEFAULT_H), Image.LANCZOS)
        bg_region = bg.crop((x, y, x + w, y + h))
        sprite    = img.convert("RGBA")
        img = Image.alpha_composite(bg_region, sprite)

    return img


def convert_file(src: Path, dst: Path, size=None, crop=None, no_resize=False,
                 on_bg: Path = None, pos=None) -> None:
    img = _open_and_prepare(src, size=size, crop=crop, no_resize=no_resize,
                            on_bg=on_bg, pos=pos)
    dst.write_bytes(_to_rgb565(img))
    w, h = img.size
    print(f"  {src.name}  →  {dst.name}  ({w}×{h}, {dst.stat().st_size:,} bytes)")


def composite_file(bg: Path, overlay: Path, dst: Path, size=None) -> None:
    """Flatten an RGBA overlay onto a background, then convert to RGB565."""
    target = size or (_DEFAULT_W, _DEFAULT_H)
    base = Image.open(bg).convert("RGBA").resize(target, Image.LANCZOS)
    top  = Image.open(overlay).convert("RGBA").resize(target, Image.LANCZOS)
    flat = Image.alpha_composite(base, top).convert("RGB")
    dst.write_bytes(_to_rgb565(flat))
    print(f"  {bg.name} + {overlay.name}  →  {dst.name}  ({dst.stat().st_size:,} bytes)")


def _parse_pair(s: str, sep: str = "x") -> tuple:
    parts = s.lower().split(sep)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"expected WxH, got {s!r}")
    return int(parts[0]), int(parts[1])


def _parse_crop(s: str) -> tuple:
    parts = s.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(f"expected x,y,w,h — got {s!r}")
    return tuple(int(p) for p in parts)


def _parse_pos(s: str) -> tuple:
    parts = s.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"expected x,y — got {s!r}")
    return int(parts[0]), int(parts[1])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PNGs to raw RGB565 for the OzSec badge GC9A01 display",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("images", nargs="+", metavar="PNG", help="Input PNG file(s)")
    parser.add_argument("--outdir", "-o", type=Path, default=None,
                        help="Output directory (default: same as input)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Explicit output path (single file)")

    # Resize / crop options (mutually exclusive)
    sizing = parser.add_mutually_exclusive_group()
    sizing.add_argument("--size", metavar="WxH", type=_parse_pair, default=None,
                        help="Output dimensions (default: 240x240 for full-screen images)")
    sizing.add_argument("--crop", metavar="x,y,w,h", type=_parse_crop, default=None,
                        help="Crop this pixel rectangle from the source")
    sizing.add_argument("--no-resize", action="store_true", default=False,
                        help="Use source image size as-is (for pre-sized sprite PNGs)")

    # Transparency / compositing
    parser.add_argument("--composite", "-c", action="store_true",
                        help="Composite two images: BACKGROUND OVERLAY  (requires --output)")
    parser.add_argument("--on-bg", metavar="BG_PNG", type=Path, default=None,
                        help="Resolve sprite transparency by compositing onto this background "
                             "at --pos.  The output sprite shows background pixels wherever "
                             "the source PNG is transparent.")
    parser.add_argument("--pos", metavar="x,y", type=_parse_pos, default=None,
                        help="Top-left position of the sprite within the --on-bg image. "
                             "Must match the on-screen position (_CHAR_X,_CHAR_Y etc.)")

    args = parser.parse_args()

    if args.composite:
        if len(args.images) != 2:
            parser.error("--composite requires exactly two images: background overlay")
        if args.output is None:
            parser.error("--composite requires --output")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        composite_file(Path(args.images[0]), Path(args.images[1]),
                       args.output, size=args.size)
        return

    if args.on_bg and args.pos is None:
        parser.error("--on-bg requires --pos x,y")

    for raw in args.images:
        src = Path(raw)
        if not src.exists():
            print(f"  [skip] not found: {src}", file=sys.stderr)
            continue
        if args.output and len(args.images) == 1:
            dst = args.output
        else:
            outdir = args.outdir or src.parent
            outdir.mkdir(parents=True, exist_ok=True)
            dst = outdir / src.with_suffix(".bin").name
        dst.parent.mkdir(parents=True, exist_ok=True)
        convert_file(src, dst, size=args.size, crop=args.crop,
                     no_resize=args.no_resize, on_bg=args.on_bg, pos=args.pos)


if __name__ == "__main__":
    main()
