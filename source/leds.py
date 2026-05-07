from machine import Pin
import neopixel
from config import PIN_LED_ALERT, PIN_LED_RAFFLE, PIN_LED_RGB, NUM_RGB_LEDS

# LED classes, a SingleLed and an RgbStrip that uses the neopixels. Split the rgb's
# into a left/right. 