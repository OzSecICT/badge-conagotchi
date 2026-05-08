#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "display.h"
#include "ws2812.h"
#include "badge_hw.h"
#include "test_buttons.h"

static const char *TAG = "button_test";

/*
 * Circular display safe-zone layout (circle r=120, center 120,120):
 *
 *  y=50  "BUTTON TEST"  scale 2, 11 chars*12=132px, x=54..186
 *        corner (54,50): dist≈94 — safe
 *  y=71  hline x=35..205
 *        corner (35,71): dist≈101 — safe
 *  Rows y=87,109,131,153,175  (5 buttons, 22px apart)
 *        at y=175 (dist=55 from cy): safe x = 120±107 → 13..227
 *        left dot x=20, right dot x=210 both verified safe
 *  y=197 hline x=35..205
 *        corner (35,197): dist≈101 — safe
 *  y=207 footer scale 1, centered — safe
 */

typedef enum {
    PHASE_TESTING,   /* tracking first-press of each button */
    PHASE_ALL_DONE,  /* all buttons seen; waiting for BOOT hold */
    PHASE_LEDS_ON,   /* all LEDs lit; waiting for BOOT press to restart */
} phase_t;

typedef struct {
    const char  *label;
    gpio_num_t   pin;
} btn_def_t;

static const btn_def_t BTNS[] = {
    {"BOOT  GPIO0",  BTN_BOOT_PIN   },
    {"START GPIO9",  BTN_START_PIN  },
    {"SEL  GPIO21",  BTN_SELECT_PIN },
    {"RGHT GPIO46",  BTN_RIGHT_PIN  },
    {"LEFT GPIO47",  BTN_LEFT_PIN   },
};
#define BTN_COUNT 5

static const int ROW_Y[BTN_COUNT] = { 87, 109, 131, 153, 175 };

/* Draw the static background (called once and on restart) */
static void draw_static(void)
{
    display_fill(COLOR_BLACK);
    display_draw_string_center(50, "BUTTON TEST", COLOR_WHITE, COLOR_BLACK, 2);
    display_draw_hline(35, 71, 170, COLOR_GRAY);

    for (int i = 0; i < BTN_COUNT; i++)
        display_draw_string_center(ROW_Y[i], BTNS[i].label, COLOR_DARKGRAY, COLOR_BLACK, 1);

    display_draw_hline(35, 197, 170, COLOR_GRAY);
    display_draw_string_center(207, "Press all buttons!", COLOR_GRAY, COLOR_BLACK, 1);
}

/* Update a single row's indicator dots and label color */
static void update_row(int i, bool pressed)
{
    uint16_t color = pressed ? COLOR_GREEN : COLOR_DARKGRAY;
    display_fill_rect(20,  ROW_Y[i], 9, 9, color);
    display_fill_rect(211, ROW_Y[i], 9, 9, color);
    display_draw_string_center(ROW_Y[i], BTNS[i].label, color, COLOR_BLACK, 1);
}

/* Replace only the footer text, leaving the hline intact */
static void update_footer(const char *text, uint16_t color)
{
    display_fill_rect(0, 198, 240, 28, COLOR_BLACK);
    display_draw_string_center(207, text, color, COLOR_BLACK, 1);
}

static void draw_celebration(void)
{
    display_fill(COLOR_BLACK);
    display_fill_circle(120, 120, 108, COLOR_DARKGRAY);
    display_draw_string_center(92,  "ALL LEDS ON!", COLOR_GREEN,  COLOR_DARKGRAY, 2);
    display_draw_hline(55, 120, 110, COLOR_GRAY);
    display_draw_string_center(133, "Press BOOT",  COLOR_YELLOW, COLOR_DARKGRAY, 1);
    display_draw_string_center(145, "to restart",  COLOR_YELLOW, COLOR_DARKGRAY, 1);
}

void test_buttons_run(void)
{
    draw_static();

    bool     prev[BTN_COUNT]         = {false};
    bool     ever_pressed[BTN_COUNT] = {false};
    int      pressed_count           = 0;
    phase_t  phase                   = PHASE_TESTING;

    ESP_LOGI(TAG, "Button test started — press all %d buttons to unlock", BTN_COUNT);

    while (1) {

        /* ── Normal button tracking (BOOT skipped in non-testing phases) ── */
        for (int i = 0; i < BTN_COUNT; i++) {
            if (phase != PHASE_TESTING && i == 0) continue;

            bool pressed = (gpio_get_level(BTNS[i].pin) == 0);
            if (pressed != prev[i]) {
                prev[i] = pressed;

                if (pressed && !ever_pressed[i]) {
                    ever_pressed[i] = true;
                    pressed_count++;
                    ESP_LOGI(TAG, "%-14s (GPIO%2d): PRESSED  [%d/%d]",
                             BTNS[i].label, BTNS[i].pin, pressed_count, BTN_COUNT);
                } else {
                    ESP_LOGI(TAG, "%-14s (GPIO%2d): %s",
                             BTNS[i].label, BTNS[i].pin, pressed ? "PRESSED" : "released");
                }
                update_row(i, pressed);
            }
        }

        /* ── Transition: all buttons pressed for the first time ── */
        if (phase == PHASE_TESTING && pressed_count == BTN_COUNT) {
            phase = PHASE_ALL_DONE;
            ESP_LOGI(TAG, "All buttons pressed! Hold BOOT to activate all LEDs");
            update_footer("Hold BOOT to unlock!", COLOR_YELLOW);
        }

        /* ── PHASE_ALL_DONE: detect BOOT held ≥500ms ── */
        if (phase == PHASE_ALL_DONE && gpio_get_level(BTN_BOOT_PIN) == 0) {
            uint64_t t0 = esp_timer_get_time();
            while (gpio_get_level(BTN_BOOT_PIN) == 0) {
                vTaskDelay(pdMS_TO_TICKS(10));
                if ((esp_timer_get_time() - t0) >= 500000ULL) {
                    /* Held long enough — light everything */
                    gpio_set_level(LED_ALERT_PIN,  1);
                    gpio_set_level(LED_RAFFLE_PIN, 1);
                    ws2812_set_all(255, 255, 255);
                    ws2812_show();
                    phase = PHASE_LEDS_ON;
                    ESP_LOGI(TAG, "BOOT held — all LEDs on. Press BOOT to restart.");
                    draw_celebration();
                    /* Wait for release so we don't immediately re-trigger */
                    while (gpio_get_level(BTN_BOOT_PIN) == 0)
                        vTaskDelay(pdMS_TO_TICKS(10));
                    break;
                }
            }
            /* If loop exited without hitting 500ms, it was a short press — ignore */
        }

        /* ── PHASE_LEDS_ON: any BOOT press restarts the full test ── */
        if (phase == PHASE_LEDS_ON && gpio_get_level(BTN_BOOT_PIN) == 0) {
            /* Debounce */
            vTaskDelay(pdMS_TO_TICKS(30));
            if (gpio_get_level(BTN_BOOT_PIN) == 0) {
                while (gpio_get_level(BTN_BOOT_PIN) == 0)
                    vTaskDelay(pdMS_TO_TICKS(10));
                /* Clean up and signal restart */
                gpio_set_level(LED_ALERT_PIN,  0);
                gpio_set_level(LED_RAFFLE_PIN, 0);
                ws2812_clear();
                ws2812_show();
                ESP_LOGI(TAG, "Restarting test sequence...");
                return;
            }
        }

        vTaskDelay(pdMS_TO_TICKS(20));
    }
}
