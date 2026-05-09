# Badge hardware pin assignments and tunable constants.
# Import this everywhere rather than hard-coding pin numbers.

# ── UART ──────────────────────────────────────────────────────────────────────
PIN_UART_TX         = 43
PIN_UART_RX         = 44

# ── I2C (SAO connector) ───────────────────────────────────────────────────────
PIN_I2C_SDA         = 17
PIN_I2C_SCL         = 18

# ── Buttons (active-low, internal pull-up) ────────────────────────────────────
PIN_BTN_BOOT        = 0
PIN_BTN_START       = 9
PIN_BTN_SELECT      = 21
PIN_BTN_RIGHT       = 46
PIN_BTN_LEFT        = 47
DEBOUNCE_MS         = 50

# ── SAO expansion GPIOs ───────────────────────────────────────────────────────
PIN_SAO_GPIO1       = 38
PIN_SAO_GPIO2       = 48

# ── LEDs ──────────────────────────────────────────────────────────────────────
PIN_LED_ALERT       = 2     # Red indicator — character needs attention
PIN_LED_RAFFLE      = 4     # Green indicator — raffle ticket earned
PIN_LED_RGB         = 45    # WS2812B data line
NUM_RGB_LEDS        = 8

# ── Display — GC9A01 240×240 round, SPI ──────────────────────────────────────
PIN_DISP_CS         = 10
PIN_DISP_MOSI       = 11    # Labelled SDA on display silkscreen
PIN_DISP_SCK        = 12    # Labelled SCL on display silkscreen
PIN_DISP_DC         = 13
PIN_DISP_RST        = 14
DISP_WIDTH          = 240
DISP_HEIGHT         = 240
DISP_SPI_FREQ       = 40_000_000

# ── IR badge-to-badge link ────────────────────────────────────────────────────
PIN_IR_TX           = 41
PIN_IR_RX           = 42
IR_FREQ_HZ          = 38_000   # matches TSOP38238 receiver

# ── Wired badge-to-badge link ─────────────────────────────────────────────────
PIN_LINK_TX         = 39
PIN_LINK_RX         = 40
LINK_BAUD           = 115200

# ── WiFi ──────────────────────────────────────────────────────────────────────
WIFI_SSID           = "OzSec 2026"
WIFI_PASSWORD       = "OzSec2026WiFi!"
WIFI_TIMEOUT_S      = 10
