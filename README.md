# OzSec 2026: Conagotchi

This is the private repository for the OzSec 2026: Conagotchi badge.

## Flashing Process
Install esptool: `pip3 install esptool`
Flash: `esptool.py --baud 460800 write_flash 0 ESP32_GENERIC_S3-20251209-v1.27.0.bin`
Install mpremote: `pip3 install mpremote`
Copy files: `mpremote cp source/