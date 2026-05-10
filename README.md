# OzSec 2026: Conagotchi

Private repository for the OzSec 2026 Conagotchi badge — an ESP32-S3 interactive badge with a round GC9A01 display, virtual pet (Conagotchi) mode, and CTF challenge mode.

## Setup

Install host tools:

```bash
pip install esptool mpremote Pillow
```

## Flashing MicroPython firmware

```bash
esptool.py --chip esp32s3 --before default-reset --after hard-reset \
    write_flash -z 0x0 firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20251209-v1.27.0.bin
```

## Deploying code

```bash
mpremote cp -r source/. :
mpremote reset
```

The VS Code default task (`Ctrl+Shift+B`) does both steps automatically.

## Converting images for the display

The GC9A01 display is 240×240 pixels round. Images must be converted from PNG to raw RGB565 binary before being copied to the badge — MicroPython cannot decode PNGs at runtime.

### Install the conversion tool dependency

```bash
pip install Pillow
```

### Full-screen backgrounds (240×240)

Design your PNG at 240×240 pixels. The corners outside the circular bezel are never shown, so no special treatment is needed — just design for a circle inscribed in the square.

```bash
python tools/convert_image.py your_image.png --outdir source/img
```

Produces `source/img/your_image.bin` — 115,200 bytes (240 × 240 × 2).

### Character animation frames

The Conagotchi idle animation uses sprite frames sized to the character bounding box (100×115 px by default). Export individual frames from your animation tool as transparent-background PNGs, then convert:

```bash
# Pre-sized PNGs (100×115) — convert without resizing
python tools/convert_image.py char_idle_0.png char_idle_1.png char_idle_2.png char_idle_3.png \
    --no-resize --outdir source/img

# OR crop from a full 240×240 mockup
python tools/convert_image.py mockup_frame0.png --crop 70,52,100,115 \
    --output source/img/char_idle_0.bin
```

The `--crop` coordinates (`x,y,w,h`) match the `_CHAR_X`, `_CHAR_Y`, `_CHAR_W`, `_CHAR_H` constants in `source/screens/conagotchi.py`.

### Menu button sprites

Each navigation button has three states: unselected (baked into the background), selected, and pressed. The selected/pressed states are small sprite files:

```bash
# Pre-sized sprite PNG
python tools/convert_image.py btn_pet_sel.png --no-resize --outdir source/img

# OR crop the button region from a full 240×240 state mockup
# Coordinates match the _BUTTONS table in source/screens/menu.py
python tools/convert_image.py menu_mockup_selected.png --crop 90,5,60,45 \
    --output source/img/btn_pet_sel.bin
```

### Compositing transparent overlays

If your overlay PNG has an alpha channel (transparency), composite it onto the background before converting:

```bash
python tools/convert_image.py background.png overlay.png \
    --composite --output source/img/result.bin
```

### Deploy images to badge

Images live in `source/img/` and are deployed alongside the Python files:

```bash
mpremote cp -r source/. :
```

### Expected image files

| File | Purpose |
|------|---------|
| `source/img/logo.bin` | Splash screen background |
| `source/img/{character}/background.bin` | Per-character main screen background (240×240) |
| `source/img/{character}/character.bin` | Idle animation base frame (80×80) |
| `source/img/{character}/idle_1.bin` … | Additional idle animation frames (optional) |
| `source/img/menu_bg.bin` | Menu screen background (all buttons unselected) |
| `source/img/btn_{id}_sel.bin` | Per-button selected state sprite |
| `source/img/btn_{id}_press.bin` | Per-button pressed state sprite |

The active character is set by `_CHARACTER` in `source/screens/conagotchi.py` (currently `"hackachi"`).

All `.bin` files are gitignored — generate them locally from your source PNGs.

## Hardware notes

- IR receiver to be changed to TSOP57438TT1 ([JLCPCB part](https://jlcpcb.com/partdetail/VishayIntertech-TSOP57438TT1/C3742825))

## Diagnostics

Run this on the REPL to check memory and flash:

```python
import gc, sys, esp32, os; gc.collect(); print(f"\n=== MicroPython Info ===\nImplementation: {sys.implementation}\nPlatform: {sys.platform}\nuname: {os.uname()}\n\n=== Memory ===\nFree: {gc.mem_free()/1024:.1f} KB\nUsed: {gc.mem_alloc()/1024:.1f} KB\nTotal: {(gc.mem_free()+gc.mem_alloc())/1024:.1f} KB\n\n=== Heap Regions ==="); [print(f"  {r[0]/1024/1024:.2f} MB total, {r[1]/1024/1024:.2f} MB free, {r[2]} largest block") for r in esp32.idf_heap_info(esp32.HEAP_DATA)]; print(f"\n=== Flash ==="); import esp; print(f"  Flash size: {esp.flash_size()/1024/1024:.0f} MB")
```
