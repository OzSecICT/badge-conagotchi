import asyncio
import gc

import display as disp
from buttons import Buttons
from leds import Leds
from screen_manager import ScreenManager
from screens.splash import SplashScreen


async def main():
    print("Badge booting...")

    display = disp.init()
    buttons = Buttons()
    leds    = Leds()

    gc.collect()
    print(f"Free RAM: {gc.mem_free()} bytes")

    mgr = ScreenManager(display, leds, buttons)
    await mgr.boot(SplashScreen())

    async def button_loop():
        while True:
            btn = await buttons.get()
            mgr.handle_button(btn)

    async def update_loop():
        while True:
            await mgr.update()
            await asyncio.sleep_ms(33)   # ~30 fps

    print("Badge ready.")
    await asyncio.gather(button_loop(), update_loop())


asyncio.run(main())
