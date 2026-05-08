#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "display.h"
#include "ws2812.h"
#include "badge_hw.h"
#include "test_leds.h"

static const char *TAG = "led_test";

#define STEP_MS 500

/* Total steps: ALERT, RAFFLE, WS2812 x8, ALL OFF = 11 steps */
#define TOTAL_STEPS 11

static void draw_step(int step, const char *led_name, bool on)
{
    display_fill(COLOR_BLACK);

    display_draw_string_center(42, "LED TEST", COLOR_WHITE, COLOR_BLACK, 2);

    char step_buf[12];
    snprintf(step_buf, sizeof(step_buf), "%d / %d", step, TOTAL_STEPS);
    display_draw_string_center(64, step_buf, COLOR_GRAY, COLOR_BLACK, 1);

    /* Short hline safely inside circle at y=78 */
    display_draw_hline(45, 78, 150, COLOR_GRAY);

    /* LED name — centered, yellow */
    display_draw_string_center(92, led_name, COLOR_YELLOW, COLOR_BLACK, 2);

    /* Big circle indicator centered at (120, 148), radius 28 */
    uint16_t ind_color = on ? COLOR_GREEN : COLOR_DARKGRAY;
    display_fill_circle(120, 148, 28, ind_color);

    /* ON / OFF text */
    display_draw_string_center(190, on ? "ON" : "OFF",
                               on ? COLOR_GREEN : COLOR_RED, COLOR_BLACK, 2);
}

void test_leds_run(void)
{
    int step = 1;

    /* Step 1: ALERT ON */
    ESP_LOGI(TAG, "Step %d/%d: ALERT LED ON (GPIO%d)", step, TOTAL_STEPS, LED_ALERT_PIN);
    gpio_set_level(LED_ALERT_PIN, 1);
    draw_step(step++, "ALERT LED", true);
    vTaskDelay(pdMS_TO_TICKS(STEP_MS));

    /* Step 2: RAFFLE ON */
    ESP_LOGI(TAG, "Step %d/%d: RAFFLE LED ON (GPIO%d)", step, TOTAL_STEPS, LED_RAFFLE_PIN);
    gpio_set_level(LED_RAFFLE_PIN, 1);
    draw_step(step++, "RAFFLE LED", true);
    vTaskDelay(pdMS_TO_TICKS(STEP_MS));

    /* Steps 3-10: WS2812 LEDs, one by one (cumulative) */
    for (int i = 0; i < WS2812_COUNT; i++) {
        ESP_LOGI(TAG, "Step %d/%d: RGB LED %d ON (GPIO%d, cumulative)",
                 step, TOTAL_STEPS, i + 1, WS2812_PIN);
        ws2812_set(i, 255, 255, 255);
        ws2812_show();
        char buf[14];
        snprintf(buf, sizeof(buf), "RGB LED %d", i + 1);
        draw_step(step++, buf, true);
        vTaskDelay(pdMS_TO_TICKS(STEP_MS));
    }

    /* Step 11: ALL OFF */
    ESP_LOGI(TAG, "Step %d/%d: ALL LEDS OFF", step, TOTAL_STEPS);
    gpio_set_level(LED_ALERT_PIN,  0);
    gpio_set_level(LED_RAFFLE_PIN, 0);
    ws2812_clear();
    ws2812_show();
    draw_step(step, "ALL LEDS", false);
    vTaskDelay(pdMS_TO_TICKS(STEP_MS));

    ESP_LOGI(TAG, "LED test complete");
    display_fill(COLOR_BLACK);
    display_fill_circle(120, 120, 50, COLOR_GREEN);
    display_draw_string_center(113, "DONE", COLOR_BLACK, COLOR_GREEN, 2);
    vTaskDelay(pdMS_TO_TICKS(800));
}
