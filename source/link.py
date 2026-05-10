import asyncio
from machine import UART, Pin
from config import (
    PIN_LINK_TX, PIN_LINK_RX, LINK_BAUD,
    PIN_IR_TX, PIN_IR_RX,
)


class WiredLink:
    """Badge-to-badge communication over the LINK connector (UART)."""

    def __init__(self):
        self._uart = UART(
            1,
            baudrate=LINK_BAUD,
            tx=Pin(PIN_LINK_TX),
            rx=Pin(PIN_LINK_RX),
        )

    def send(self, data: bytes):
        self._uart.write(data)

    def available(self) -> int:
        return self._uart.any()

    def read(self, n: int = -1) -> bytes:
        return self._uart.read(n)

    async def read_line(self) -> str:
        buf = b""
        while True:
            if self._uart.any():
                ch = self._uart.read(1)
                if ch == b"\n":
                    return buf.decode()
                buf += ch
            else:
                await asyncio.sleep_ms(10)


class IrLink:
    """Badge-to-badge IR communication (stub — implementation TBD)."""

    def __init__(self):
        self._tx = Pin(PIN_IR_TX, Pin.OUT, value=0)
        self._rx = Pin(PIN_IR_RX, Pin.IN)

    def send(self, data: bytes):
        # TODO: implement IR modulation at IR_FREQ_HZ
        raise NotImplementedError

    def available(self) -> bool:
        # TODO: implement IR receive
        raise NotImplementedError
