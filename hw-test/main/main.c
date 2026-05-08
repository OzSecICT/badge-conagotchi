#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "display.h"
#include "ws2812.h"
#include "badge_hw.h"
#include "test_display.h"
#include "test_leds.h"
#include "test_buttons.h"

static const char *TAG = "main";

static void init_buttons(void)
{
    const gpio_num_t btns[] = {
        BTN_BOOT_PIN, BTN_START_PIN, BTN_SELECT_PIN,
        BTN_RIGHT_PIN, BTN_LEFT_PIN,
    };
    for (int i = 0; i < (int)(sizeof(btns) / sizeof(btns[0])); i++) {
        gpio_config_t io = {
            .pin_bit_mask = 1ULL << btns[i],
            .mode         = GPIO_MODE_INPUT,
            .pull_up_en   = GPIO_PULLUP_ENABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        gpio_config(&io);
    }
}

static void init_leds(void)
{
    gpio_config_t io = {
        .pin_bit_mask = (1ULL << LED_ALERT_PIN) | (1ULL << LED_RAFFLE_PIN),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&io);
    gpio_set_level(LED_ALERT_PIN,  0);
    gpio_set_level(LED_RAFFLE_PIN, 0);
}

void app_main(void)
{
    ESP_LOGI(TAG, "Badge HW Test v2 starting");

    init_buttons();
    init_leds();
    display_init();
    ws2812_init();

    while (1) {
        test_display_run();   /* Auto-cycles 8 display patterns     */
        test_leds_run();      /* Auto-sequences all LEDs, 500ms each */
        test_buttons_run();   /* Returns when BOOT pressed in leds-on state */
        ESP_LOGI(TAG, "--- Test sequence restarting ---");
    }
}
