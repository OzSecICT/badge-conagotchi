# config.py
# Contains configuration info such as pin assignments.

# WiFi
WIFI_SSID           = "OzSec 2026"
WIFI_PASSWORD       = "OzSec2026WiFi!"

# UART
PIN_UART_TX         = 43
PIN_UART_RX         = 44

# I2C PINs exposed on the SAO connector
PIN_I2C_SDA         = 17
PIN_I2C_SCL         = 18

# Buttons
PIN_BTN_BOOT        = 0
PIN_BTN_START       = 9
PIN_BTN_SELECT      = 21
PIN_BTN_RIGHT       = 46
PIN_BTN_LEFT        = 47

# SAO GPIOs, un-used but available for the user to implement.
PIN_SAO_GPIO1       = 38
PIN_SAO_GPIO2       = 48

# LEDs
PIN_LED_ALERT       = 2    # This LED is lit up when the character needs something
PIN_LED_RAFFLE      = 4    # This LED is lit up when enough badge challenges are completed to earn a raffle ticket entry
PIN_LED_RGB         = 45   # WS2812B data line

NUM_RGB_LEDS        = 8    # number of LEDs on the strip

# Display — SPI (GC9A01 round 240x240)
PIN_DISPLAY_CS      = 10
PIN_DISPLAY_MOSI    = 11   # SDA on display silkscreen
PIN_DISPLAY_SCK     = 12   # SCL on display silkscreen
PIN_DISPLAY_DC      = 13
PIN_DISPLAY_RST     = 14

DISPLAY_WIDTH       = 240
DISPLAY_HEIGHT      = 240

# IR link (badge-to-badge)
PIN_IR_TX           = 41
PIN_IR_RX           = 42

IR_FREQ_HZ          = 38_000   # 38kHz carrier for TSOP38238 receiver

# Wired link connector for badge-to-badge communication
PIN_LINK_TX         = 39
PIN_LINK_RX         = 40
