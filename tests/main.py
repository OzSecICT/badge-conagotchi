import machine
import time
import neopixel
import network
import gc9a01py as gc9a01
import config
from buttons import Buttons

# Simple display logger for circular screen
class DisplayLogger:
    def __init__(self, tft):
        self.tft = tft
        self.lines = []
        self.max_lines = 8
        self.y_start = 60
        self.line_height = 16
        
    def log(self, message):
        print(message)  # Still print to serial
        self.lines.append(message)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        self.draw()
        
    def draw(self):
        self.tft.fill(gc9a01.BLACK)
        # Try to draw a circular boundary
        # self.tft.circle(120, 120, 119, gc9a01.WHITE)
        
        y = self.y_start
        for line in self.lines:
            # We use a fallback if text() fails without a font
            try:
                # Some drivers have a default font if None is passed
                # If it still fails, we'll draw a small bar or just ignore
                self.tft.text(None, line[:20], 40, y, gc9a01.CYAN)
            except:
                # Fallback: draw a small rectangle for each log line to show activity
                self.tft.rect(40, y, 10, 10, gc9a01.GREEN)
            y += self.line_height

def init_hw():
    spi = machine.SPI(1,
                      baudrate=config.DISPLAY_SPI_FREQ,
                      sck=machine.Pin(config.PIN_DISPLAY_SCK),
                      mosi=machine.Pin(config.PIN_DISPLAY_MOSI))
    tft = gc9a01.GC9A01(spi,
                        dc=machine.Pin(config.PIN_DISPLAY_DC),
                        cs=machine.Pin(config.PIN_DISPLAY_CS),
                        reset=machine.Pin(config.PIN_DISPLAY_RST),
                        rotation=0)
    try:
        tft.init()
    except AttributeError:
        pass
    return tft

def test_display(tft, logger):
    logger.log("Testing Display...")
    colors = [gc9a01.RED, gc9a01.GREEN, gc9a01.BLUE]
    for c in colors:
        tft.fill(c)
        time.sleep_ms(200)
    tft.fill(gc9a01.BLACK)
    logger.log("Display OK")

def test_leds(logger):
    logger.log("Testing LEDs...")
    alert = machine.Pin(config.PIN_LED_ALERT, machine.Pin.OUT)
    raffle = machine.Pin(config.PIN_LED_RAFFLE, machine.Pin.OUT)
    
    for i in range(3):
        logger.log(f"Flash {i+1}...")
        alert.value(1)
        raffle.value(0)
        time.sleep_ms(150)
        alert.value(0)
        raffle.value(1)
        time.sleep_ms(150)
    alert.value(0)
    raffle.value(0)
    
    try:
        np = neopixel.NeoPixel(machine.Pin(config.PIN_LED_RGB), config.NUM_RGB_LEDS)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for c_name, color in zip(["RED", "GREEN", "BLUE"], colors):
            logger.log(f"RGB: {c_name}")
            for i in range(config.NUM_RGB_LEDS):
                np[i] = color
            np.write()
            time.sleep_ms(300)
        # Clear
        for i in range(config.NUM_RGB_LEDS):
            np[i] = (0, 0, 0)
        np.write()
        logger.log("LEDs OK")
    except Exception as e:
        logger.log(f"RGB Error: {str(e)[:15]}")

def test_wifi(logger):
    logger.log("WiFi Scan...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        nets = wlan.scan()
        logger.log(f"Found {len(nets)} nets")
        # Log first 2 SSIDs
        for n in nets[:2]:
            ssid = n[0].decode('utf-8')[:15]
            logger.log(f" {ssid}")
    except Exception as e:
        logger.log(f"WiFi Fail: {str(e)[:15]}")

def test_i2c(logger):
    logger.log("I2C Scan (SAO)...")
    try:
        i2c = machine.I2C(0, 
                          sda=machine.Pin(config.PIN_I2C_SDA), 
                          scl=machine.Pin(config.PIN_I2C_SCL), 
                          freq=config.I2C_FREQ)
        devs = i2c.scan()
        logger.log(f"Devs: {len(devs)}")
        for d in devs:
            logger.log(f" Addr: {hex(d)}")
    except Exception as e:
        logger.log(f"I2C Fail: {str(e)[:15]}")

def test_buttons(tft, logger):
    logger.log("BTN Test: BOOT to exit")
    buttons = Buttons()
    start_time = time.ticks_ms()
    
    while True:
        event = buttons.get_event()
        if event:
            logger.log(f"Pressed: {event}")
            if event == "BOOT":
                break
        
        # Timeout after 20 seconds
        if time.ticks_diff(time.ticks_ms(), start_time) > 20000:
            logger.log("BTN Timeout")
            break
        time.sleep_ms(50)

def main():
    # Ensure we can import from source/
    import sys
    if "/source" not in sys.path:
        sys.path.append("/source")
        
    tft = init_hw()
    logger = DisplayLogger(tft)
    
    logger.log("OZSEC 2026 TEST")
    time.sleep(1)
    
    test_display(tft, logger)
    test_leds(logger)
    test_wifi(logger)
    test_i2c(logger)
    
    # Interactive test last
    test_buttons(tft, logger)
    
    logger.log("ALL TESTS DONE")
    time.sleep(2)
    tft.fill(gc9a01.GREEN)
    try:
        tft.text(None, "PASS", 100, 110, gc9a01.BLACK)
    except:
        pass

if __name__ == "__main__":
    main()
