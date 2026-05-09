import asyncio
import gc

import display as disp
from buttons import Buttons, START, SELECT, LEFT, RIGHT, BOOT
from leds import Leds


async def main():
    print("Badge booting...")

    # ── Hardware init ──────────────────────────────────────────────────────
    display = disp.init()
    buttons = Buttons()
    leds    = Leds()

    gc.collect()
    print(f"Free RAM: {gc.mem_free()} bytes")

    # ── Main event loop ────────────────────────────────────────────────────
    print("Badge ready.")
    while True:
        btn = await buttons.get()
        print(f"Button: {btn}")

        if btn == START:
            pass  # TODO: confirm / enter menu item

        elif btn == SELECT:
            pass  # TODO: open menu / back

        elif btn == LEFT:
            pass  # TODO: navigate left

        elif btn == RIGHT:
            pass  # TODO: navigate right

        elif btn == BOOT:
            pass  # TODO: reserved / debug

        gc.collect()


asyncio.run(main())
