# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OzSec 2026 Conagotchi Badge — an ESP32-S3 interactive hardware badge running MicroPython. Features a round GC9A01 display, 5 buttons, RGB LEDs, badge-to-badge IR/UART comms, and WiFi. Has two modes: a Conagotchi (virtual-pet) mode and a CTF/challenge mode.

## Development Workflow

### Prerequisites

```bash
pip install esptool mpremote Pillow
```

### Deploy Code to Badge

```bash
mpremote cp -r source/. :    # Copy all source files (including source/img/*.bin)
mpremote reset
```

The default VS Code task (`Ctrl+Shift+B`) runs deploy + reset together.

### Convert PNG images for the display

```bash
python tools/convert_image.py assets/logo.png --outdir source/img
# Composite an RGBA overlay onto a background:
python tools/convert_image.py bg.png overlay.png --composite --output source/img/menu_bg.bin
```

Output is raw big-endian RGB565 binary (240×240×2 = 115,200 bytes). See **Image Workflow** below.

### Flash MicroPython Firmware

```bash
esptool.py --chip esp32s3 --before default-reset --after hard-reset write_flash -z 0x0 firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20251209-v1.27.0.bin
```

### Hardware Validation (C/ESP-IDF, optional)

```bash
cd hw-test/
. ~/.espressif/v6.0/esp-idf/export.sh
idf.py build flash monitor
```

### Type Checking

Pyright is configured in `pyrightconfig.json` (basic mode). Type stubs for MicroPython modules live in `typings/`.

## Architecture

The firmware is async/event-driven, built on MicroPython's `asyncio`. Two concurrent tasks run in `main.py`: a `button_loop` and an `update_loop` (~30 fps).

### Screen / UI system

Navigation uses a **screen stack** managed by `ScreenManager` (`source/screen_manager.py`):

| Call | Effect |
|------|--------|
| `mgr.push(screen)` | Overlay a new screen (e.g. open a menu) |
| `mgr.pop()` | Return to the screen below |
| `mgr.switch_to(screen)` | Replace the entire stack |

Screens subclass `Screen` and override `enter / exit / pause / resume / update / handle_button`. Transitions are requested synchronously from `handle_button()` and executed asynchronously on the next `update()` tick.

Current screens:

- **`screens/splash.py`** — boot logo; auto-advances to ConagotchiScreen after 3 s
- **`screens/conagotchi.py`** — main pet idle screen; SELECT opens MainMenu
- **`screens/menu.py`** — bottom-arc overlay menu (Pet / CTF / Settings)

Add new screens under `source/screens/`. Use lazy imports (`from screens.foo import Foo` inside functions) to avoid circular imports and save boot RAM.

### Image workflow

MicroPython cannot decode PNG at runtime. The pipeline is:

1. Design PNGs at **240×240 px** (corners are hidden by the round bezel — no special treatment needed)
2. Run `tools/convert_image.py` on the host → produces raw RGB565 `.bin` files in `source/img/`
3. Deploy with `mpremote cp -r source/. :` — the `img/` directory is included automatically
4. In MicroPython: `image_utils.blit_image(display, "img/logo.bin")`

For **layered/transparent designs** (e.g. menu background over conagotchi screen): use `--composite bg.png overlay.png --output out.bin` to pre-flatten before converting. The driver has no runtime alpha-blending.

#### Menu button sprites

The menu uses a **three-state sprite system** for buttons positioned at the top and bottom arcs of the display:

- `img/menu_bg.bin` — full 240×240 background with all buttons in **unselected** state
- `img/btn_{id}_sel.bin` — button **selected** sprite (w×h pixels, no header)
- `img/btn_{id}_press.bin` — button **pressed** sprite (w×h pixels, no header)

Button positions (`x, y, w, h`) are defined in `_BUTTONS` at the top of `source/screens/menu.py` and **must match the pixel coordinates in `menu_bg.png`**. Update these constants when artwork is finalised.

**Converting sprite images** — two options:

```bash
# Option A: pre-sized PNG for each button state (use exact pixel dimensions)
python tools/convert_image.py btn_pet_sel.png --no-resize --outdir source/img

# Option B: design in full 240×240 mockups, crop the button region out
#   --crop x,y,w,h  matches the _BUTTONS table entry for that button
python tools/convert_image.py menu_pet_sel_full.png --crop 90,5,60,45 \
    --output source/img/btn_pet_sel.bin
```

**On-device rendering** — when a button's state changes, only its bounding box is redrawn:
- Deselect: `image_utils.restore_from_bg()` seeks the background file row-by-row (no large allocation)
- Select / press: `image_utils.blit_sprite()` loads and blits the small sprite file

#### Character idle animation

The Conagotchi uses `SpriteAnim` (`source/anim.py`) for the character animation. Frames are small sprites blitted at the character bounding box; the background is restored between frames via `restore_from_bg()`.

- Frame files: `img/char_idle_0.bin` … `img/char_idle_N.bin` (sized `_CHAR_W × _CHAR_H`, currently 100×115)
- Speed / frame count / mode are constants at the top of `source/screens/conagotchi.py`
- A primitive fallback (breathing bob + blink) runs when sprite files are absent

**Recommended tool: [Aseprite](https://www.aseprite.org/)**  
Create a 100×115 canvas (transparent background), animate, then export individual frames:  
*File → Export Sprite Sheet → type: "By Frame" → PNG files*

```bash
# Convert each exported frame (pre-sized 100×115 PNGs)
python tools/convert_image.py char_idle_0.png char_idle_1.png char_idle_2.png char_idle_3.png \
    --no-resize --outdir source/img

# OR crop from a full 240×240 mockup (x,y,w,h matches _CHAR_X,_CHAR_Y,_CHAR_W,_CHAR_H)
python tools/convert_image.py mockup_idle_0.png --crop 70,52,100,115 \
    --output source/img/char_idle_0.bin
```

Expected image paths on the badge filesystem:

| File | Purpose |
|------|---------|
| `img/logo.bin` | SplashScreen background |
| `img/bg_main.bin` | ConagotchiScreen background |
| `img/char_idle_0.bin` … `img/char_idle_N.bin` | Character idle animation frames |
| `img/menu_bg.bin` | MainMenu background (all buttons unselected) |
| `img/btn_{id}_sel.bin` | Per-button selected sprite |
| `img/btn_{id}_press.bin` | Per-button pressed sprite |

All `.bin` files are gitignored (derived from source PNGs).

### Core modules

**`source/config.py`** — single source of truth for all GPIO pins, baud rates, and tunable constants.

**`source/image_utils.py`** — `blit_image()` (streams RGB565 file to display) and `draw_text()` (renders text using framebuf's built-in 8×8 font with endian correction for gc9a01py).

**`source/buttons.py`** — ISR-driven debounced button handler; presses are queued for `buttons.get()`.

**`source/leds.py`** — red alert LED, green raffle LED, 8×WS2812B RGB strip.

**`source/display.py`** — GC9A01 SPI init. Driver (`gc9a01py.py`) uses big-endian `">H"` RGB565 — important when pre-computing image data.

**`source/link.py`** — `WiredLink` (UART, working) and `IrLink` (IR, stub/TODO).

**`source/wifi.py`** — async WiFi connect/disconnect helper.

## Known TODOs

- `IrLink.send()` / `IrLink.available()` in `link.py` — unimplemented
- ConagotchiScreen: real pet state model, idle animations, action menu (feed/drink/play/sleep)
- `screens/menu.py` `_activate()`: wire up CTF and Settings screens when built
- Hardware: IR receiver to be changed to TSOP57438TT1

## Hardware Reference

Pin assignments: `hardware/pinout.txt`  
Schematics/PCB: `hardware/kicad/OzSec2026-ESP32/`  
Target: ESP32-S3, 8 MB Octal PSRAM, MicroPython v1.27.0
