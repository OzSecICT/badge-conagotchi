idf_component_register(
    SRCS
        "main.c"
        "display.c"
        "ws2812.c"
        "test_display.c"
        "test_leds.c"
        "test_buttons.c"
    INCLUDE_DIRS "."
    REQUIRES
        esp_driver_gpio
        esp_driver_spi
        esp_driver_rmt
        esp_timer
        freertos
        log
)
