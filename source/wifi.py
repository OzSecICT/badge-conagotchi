import asyncio
import network
from config import WIFI_SSID, WIFI_PASSWORD, WIFI_TIMEOUT_S


class Wifi:
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)

    async def connect(self) -> bool:
        """Attempt to connect; return True on success."""
        self._wlan.active(True)
        if self._wlan.isconnected():
            return True

        self._wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(WIFI_TIMEOUT_S * 10):
            if self._wlan.isconnected():
                print("WiFi connected:", self._wlan.ifconfig())
                return True
            await asyncio.sleep_ms(100)

        print("WiFi connect timeout")
        return False

    def disconnect(self):
        self._wlan.disconnect()
        self._wlan.active(False)

    @property
    def connected(self) -> bool:
        return self._wlan.isconnected()

    @property
    def ip(self) -> str:
        return self._wlan.ifconfig()[0] if self.connected else ""
