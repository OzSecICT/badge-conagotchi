#pragma once

#include "driver/gpio.h"

/* Display SPI */
#define DISP_CS_PIN     GPIO_NUM_10
#define DISP_MOSI_PIN   GPIO_NUM_11
#define DISP_SCK_PIN    GPIO_NUM_12
#define DISP_DC_PIN     GPIO_NUM_13
#define DISP_RST_PIN    GPIO_NUM_14
#define DISP_SPI_HOST   SPI2_HOST
#define DISP_SPI_FREQ   40000000
#define DISP_WIDTH      240
#define DISP_HEIGHT     240

/* Buttons — active low with internal pull-up */
#define BTN_BOOT_PIN    GPIO_NUM_0
#define BTN_START_PIN   GPIO_NUM_9
#define BTN_SELECT_PIN  GPIO_NUM_21
#define BTN_RIGHT_PIN   GPIO_NUM_46
#define BTN_LEFT_PIN    GPIO_NUM_47

/* LEDs — active high */
#define LED_ALERT_PIN   GPIO_NUM_2
#define LED_RAFFLE_PIN  GPIO_NUM_4

/* WS2812B */
#define WS2812_PIN      GPIO_NUM_45
#define WS2812_COUNT    8

/* Colors (RGB565) */
#define COLOR_BLACK     0x0000
#define COLOR_WHITE     0xFFFF
#define COLOR_RED       0xF800
#define COLOR_GREEN     0x07E0
#define COLOR_BLUE      0x001F
#define COLOR_YELLOW    0xFFE0
#define COLOR_CYAN      0x07FF
#define COLOR_MAGENTA   0xF81F
#define COLOR_ORANGE    0xFC00
#define COLOR_GRAY      0x7BEF
#define COLOR_DARKGRAY  0x39E7

typedef enum {
    SCREEN_MAIN_MENU = 0,
    SCREEN_DISPLAY_TEST,
    SCREEN_LED_TEST,
    SCREEN_BUTTON_TEST,
} screen_t;
