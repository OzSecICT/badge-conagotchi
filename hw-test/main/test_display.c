#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "display.h"
#include "badge_hw.h"
#include "test_display.h"

static const char *TAG = "display_test";

#define PATTERN_DWELL_MS 1500

static void draw_checkerboard(void)
{
    const int sq = 30;
    for (int y = 0; y < DISP_HEIGHT; y += sq) {
        for (int x = 0; x < DISP_WIDTH; x += sq) {
            uint16_t color = ((x / sq + y / sq) % 2) ? COLOR_WHITE : COLOR_BLACK;
            display_fill_rect(x, y, sq, sq, color);
        }
    }
}

static void draw_color_bars(void)
{
    uint16_t bars[] = {
        COLOR_RED, COLOR_GREEN, COLOR_BLUE,
        COLOR_YELLOW, COLOR_CYAN, COLOR_MAGENTA,
        COLOR_WHITE, COLOR_BLACK,
    };
    int n = sizeof(bars) / sizeof(bars[0]);
    int bar_w = DISP_WIDTH / n;
    for (int i = 0; i < n; i++)
        display_fill_rect(i * bar_w, 0, bar_w, DISP_HEIGHT, bars[i]);
}

static void draw_gradient(void)
{
    for (int x = 0; x < DISP_WIDTH; x++) {
        uint8_t r = (x * 31) / (DISP_WIDTH - 1);
        uint16_t color = (r << 11);
        display_draw_vline(x, 0, DISP_HEIGHT / 3, color);
    }
    for (int x = 0; x < DISP_WIDTH; x++) {
        uint8_t g = (x * 63) / (DISP_WIDTH - 1);
        uint16_t color = (g << 5);
        display_draw_vline(x, DISP_HEIGHT / 3, DISP_HEIGHT / 3, color);
    }
    for (int x = 0; x < DISP_WIDTH; x++) {
        uint8_t b = (x * 31) / (DISP_WIDTH - 1);
        uint16_t color = b;
        display_draw_vline(x, (DISP_HEIGHT * 2) / 3, DISP_HEIGHT / 3, color);
    }
}

static void draw_crosshair(void)
{
    display_fill(COLOR_BLACK);
    display_draw_hline(0, DISP_HEIGHT / 2, DISP_WIDTH, COLOR_WHITE);
    display_draw_vline(DISP_WIDTH / 2, 0, DISP_HEIGHT, COLOR_WHITE);
    display_draw_rect(0, 0, DISP_WIDTH, DISP_HEIGHT, COLOR_WHITE);
    display_draw_rect(10, 10, DISP_WIDTH - 20, DISP_HEIGHT - 20, COLOR_GRAY);
    display_draw_string(60, 110, "CROSSHAIR", COLOR_YELLOW, COLOR_BLACK, 2);
}

void test_display_run(void)
{
    typedef struct { const char *name; void (*fn)(void); } pattern_t;

    pattern_t patterns[] = {
        {"RED FILL",    NULL},
        {"GREEN FILL",  NULL},
        {"BLUE FILL",   NULL},
        {"WHITE FILL",  NULL},
        {"CHECKER",     draw_checkerboard},
        {"COLOR BARS",  draw_color_bars},
        {"GRADIENT",    draw_gradient},
        {"CROSSHAIR",   draw_crosshair},
    };
    uint16_t solid_colors[] = {
        COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_WHITE, 0, 0, 0, 0
    };

    int n = (int)(sizeof(patterns) / sizeof(patterns[0]));
    for (int i = 0; i < n; i++) {
        ESP_LOGI(TAG, "Pattern %d/%d: %s", i + 1, n, patterns[i].name);
        if (patterns[i].fn) {
            patterns[i].fn();
        } else {
            display_fill(solid_colors[i]);
        }
        /* Dark band in the safe center zone, then centered label */
        display_fill_rect(30, 107, 180, 18, COLOR_BLACK);
        display_draw_string_center(109, patterns[i].name, COLOR_WHITE, COLOR_BLACK, 2);
        vTaskDelay(pdMS_TO_TICKS(PATTERN_DWELL_MS));
    }

    ESP_LOGI(TAG, "Display test complete");
    display_fill(COLOR_BLACK);
    display_draw_string_center(108, "TEST DONE", COLOR_GREEN, COLOR_BLACK, 2);
    display_draw_string_center(130, "Returning...", COLOR_GRAY, COLOR_BLACK, 2);
    vTaskDelay(pdMS_TO_TICKS(1000));
}
