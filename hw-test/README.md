# OzSec 2026 Badge — Hardware Test

ESP-IDF project for validating badge hardware before firmware development.
Targets the ESP32-S3 with Octal PSRAM.

## What It Tests

The test runs automatically in sequence on boot:

### 1. Display Test
Cycles through 8 visual patterns on the GC9A01 round 240×240 display,
dwelling 1.5 seconds on each before returning automatically:
- Solid fills: Red, Green, Blue, White
- Checkerboard
- Color bars
- RGB gradient
- Crosshair with border

### 2. LED Sequence
Turns on each LED one at a time with 500ms between steps, then turns
them all off:
- ALERT LED (GPIO2)
- RAFFLE LED (GPIO4)
- WS2812B RGB strip (GPIO45) — 8 LEDs lit individually and cumulatively

### 3. Button Test (interactive)
Displays live press/release status for all five buttons. Indicator dots
and label text turn green when a button is held.

- **BOOT** — GPIO0
- **START** — GPIO9
- **SELECT** — GPIO21
- **RIGHT** — GPIO46
- **LEFT** — GPIO47

Once every button has been pressed at least once, the footer prompts
**Hold BOOT to unlock**. Holding BOOT for 500ms turns on all LEDs and
the full WS2812B strip (white). Pressing BOOT again restarts the entire
test sequence from the beginning.

All steps are logged over serial at 115200 baud.

---

## Prerequisites

### Install ESP-IDF with EIM

Espressif IDF Manager (EIM) is the recommended way to install and manage
ESP-IDF versions on macOS and Windows. Download it from:

**https://idf.espressif.com/**

After installing and launching EIM:
1. Select **ESP-IDF v6.0** (or later) and click Install
2. EIM installs the framework and toolchain to `~/.espressif/`

To activate the environment in a terminal session:

```bash
. ~/.espressif/v6.0/esp-idf/export.sh
```

Add an alias to `~/.zshrc` to make this convenient:

```bash
alias get_idf='. ~/.espressif/v6.0/esp-idf/export.sh'
```

> The `export.sh` path will reflect the version EIM installed. Adjust
> `v6.0` if you installed a different version.

---

## Building and Flashing

All commands below should be run from the `hw-test/` directory with the
IDF environment activated.

### Normal build (PSRAM enabled)

```bash
idf.py build flash monitor
```

On first build, or after deleting `sdkconfig`:

```bash
idf.py reconfigure build flash monitor
```

### No-PSRAM build (for boards with faulty or absent PSRAM)

If a board boot-loops with the standard build, its PSRAM is likely
non-functional. Flash a PSRAM-disabled binary:

```bash
rm -f sdkconfig && idf.py -DSDKCONFIG_DEFAULTS=sdkconfig.defaults.nopsram build flash monitor
```

To return to the PSRAM-enabled build afterwards:

```bash
rm -f sdkconfig && idf.py build flash monitor
```

> `rm -f sdkconfig` is required when switching between variants because
> the existing `sdkconfig` file takes precedence over all defaults files.
> Deleting it forces a clean regeneration.

### Flashing note

The badge uses the ESP32-S3 built-in USB (GPIO19/GPIO20). Auto-reset
into download mode is enabled via `CONFIG_ESPTOOLPY_BEFORE="usb_reset"`
in `sdkconfig.defaults` — no manual boot+reset should be required once
firmware is running.

If the board is in a boot loop (and USB never initialises), you will
still need to hold **BOOT + RESET** to enter download mode manually for
that first flash.

---

## Serial Monitor

`idf.py monitor` connects at 115200 baud. Each test phase logs progress:

```
I (xxx) display_test: Pattern 1/8: RED FILL
I (xxx) led_test:     Step 3/11: RGB LED 1 ON (GPIO45, cumulative)
I (xxx) button_test:  START GPIO9   (GPIO 9): PRESSED
I (xxx) button_test:  All buttons pressed! Hold BOOT to activate all LEDs
```

Exit the monitor with **Ctrl+]**.

---

## Pin Reference

| Function     | GPIO |
|--------------|------|
| Display CS   | 10   |
| Display MOSI | 11   |
| Display SCK  | 12   |
| Display DC   | 13   |
| Display RST  | 14   |
| BOOT button  | 0    |
| START button | 9    |
| SELECT button| 21   |
| RIGHT button | 46   |
| LEFT button  | 47   |
| ALERT LED    | 2    |
| RAFFLE LED   | 4    |
| RGB strip    | 45   |
