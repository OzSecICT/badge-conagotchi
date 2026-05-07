# OzSec 2026: Conagotchi

This is the private repository for the OzSec 2026: Conagotchi badge.

## Flashing Process
Install esptool: `pip3 install esptool`
Flash: `esptool.py --baud 460800 write_flash 0 ESP32_GENERIC_S3-20251209-v1.27.0.bin`
Install mpremote: `pip3 install mpremote`
Copy files: `mpremote cp source



## To Do
Change THT IR receiver to https://jlcpcb.com/partdetail/VishayIntertech-TSOP57438TT1/C3742825


Testing: 
```
import gc, sys, esp32, os; gc.collect(); print(f"\n=== MicroPython Info ===\nImplementation: {sys.implementation}\nPlatform: {sys.platform}\nuname: {os.uname()}\n\n=== Memory ===\nFree: {gc.mem_free()/1024:.1f} KB\nUsed: {gc.mem_alloc()/1024:.1f} KB\nTotal: {(gc.mem_free()+gc.mem_alloc())/1024:.1f} KB\n\n=== Heap Regions ==="); [print(f"  {r[0]/1024/1024:.2f} MB total, {r[1]/1024/1024:.2f} MB free, {r[2]} largest block") for r in esp32.idf_heap_info(esp32.HEAP_DATA)]; print(f"\n=== Flash ==="); import esp; print(f"  Flash size: {esp.flash_size()/1024/1024:.0f} MB")
```