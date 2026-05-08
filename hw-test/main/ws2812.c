#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/rmt_tx.h"
#include "driver/rmt_encoder.h"
#include "esp_log.h"
#include "badge_hw.h"
#include "ws2812.h"

static const char *TAG = "ws2812";

/* WS2812B timing (ns) */
#define WS2812_T0H_NS   350
#define WS2812_T0L_NS   800
#define WS2812_T1H_NS   700
#define WS2812_T1L_NS   600
#define WS2812_RESET_NS 50000

#define RMT_CLK_RESOLUTION 10000000  /* 10 MHz = 100ns per tick */

static rmt_channel_handle_t rmt_chan = NULL;
static rmt_encoder_handle_t rmt_enc  = NULL;

static uint8_t led_buf[WS2812_COUNT * 3]; /* GRB order */

/* Simple bytes encoder wrapping a copy encoder + reset symbol */
typedef struct {
    rmt_encoder_t  base;
    rmt_encoder_t *bytes_encoder;
    rmt_encoder_t *copy_encoder;
    int            state;
    rmt_symbol_word_t reset_code;
} ws2812_encoder_t;

static size_t ws2812_encode(rmt_encoder_t *encoder, rmt_channel_handle_t channel,
                             const void *primary_data, size_t data_size,
                             rmt_encode_state_t *ret_state)
{
    ws2812_encoder_t *enc = __containerof(encoder, ws2812_encoder_t, base);
    rmt_encode_state_t session_state = RMT_ENCODING_RESET;
    size_t encoded = 0;

    if (enc->state == 0) {
        size_t n = enc->bytes_encoder->encode(enc->bytes_encoder, channel,
                                              primary_data, data_size, &session_state);
        encoded += n;
        if (session_state & RMT_ENCODING_COMPLETE) {
            enc->state = 1;
            session_state = RMT_ENCODING_RESET;
        }
        if (session_state & RMT_ENCODING_MEM_FULL) {
            *ret_state = RMT_ENCODING_MEM_FULL;
            return encoded;
        }
    }
    if (enc->state == 1) {
        size_t n = enc->copy_encoder->encode(enc->copy_encoder, channel,
                                             &enc->reset_code, sizeof(rmt_symbol_word_t),
                                             &session_state);
        encoded += n;
        if (session_state & RMT_ENCODING_COMPLETE) {
            enc->state = RMT_ENCODING_RESET;
            session_state = RMT_ENCODING_COMPLETE;
        }
    }
    *ret_state = session_state;
    return encoded;
}

static esp_err_t ws2812_del(rmt_encoder_t *encoder)
{
    ws2812_encoder_t *enc = __containerof(encoder, ws2812_encoder_t, base);
    rmt_del_encoder(enc->bytes_encoder);
    rmt_del_encoder(enc->copy_encoder);
    free(enc);
    return ESP_OK;
}

static esp_err_t ws2812_reset(rmt_encoder_t *encoder)
{
    ws2812_encoder_t *enc = __containerof(encoder, ws2812_encoder_t, base);
    rmt_encoder_reset(enc->bytes_encoder);
    rmt_encoder_reset(enc->copy_encoder);
    enc->state = 0;
    return ESP_OK;
}

static void create_ws2812_encoder(void)
{
    ws2812_encoder_t *enc = calloc(1, sizeof(ws2812_encoder_t));

    rmt_bytes_encoder_config_t bcfg = {
        .bit0 = {
            .level0 = 1,
            .duration0 = WS2812_T0H_NS / (1000000000 / RMT_CLK_RESOLUTION),
            .level1 = 0,
            .duration1 = WS2812_T0L_NS / (1000000000 / RMT_CLK_RESOLUTION),
        },
        .bit1 = {
            .level0 = 1,
            .duration0 = WS2812_T1H_NS / (1000000000 / RMT_CLK_RESOLUTION),
            .level1 = 0,
            .duration1 = WS2812_T1L_NS / (1000000000 / RMT_CLK_RESOLUTION),
        },
        .flags.msb_first = 1,
    };
    rmt_new_bytes_encoder(&bcfg, &enc->bytes_encoder);

    rmt_copy_encoder_config_t ccfg = {};
    rmt_new_copy_encoder(&ccfg, &enc->copy_encoder);

    uint32_t reset_ticks = RMT_CLK_RESOLUTION / 1000000 * WS2812_RESET_NS / 1000;
    enc->reset_code = (rmt_symbol_word_t){
        .level0 = 0, .duration0 = reset_ticks / 2,
        .level1 = 0, .duration1 = reset_ticks / 2,
    };

    enc->base.encode   = ws2812_encode;
    enc->base.del      = ws2812_del;
    enc->base.reset    = ws2812_reset;
    rmt_enc = &enc->base;
}

void ws2812_init(void)
{
    rmt_tx_channel_config_t cfg = {
        .gpio_num        = WS2812_PIN,
        .clk_src         = RMT_CLK_SRC_DEFAULT,
        .resolution_hz   = RMT_CLK_RESOLUTION,
        .mem_block_symbols = 64,
        .trans_queue_depth = 4,
    };
    ESP_ERROR_CHECK(rmt_new_tx_channel(&cfg, &rmt_chan));
    create_ws2812_encoder();
    ESP_ERROR_CHECK(rmt_enable(rmt_chan));
    memset(led_buf, 0, sizeof(led_buf));
    ESP_LOGI(TAG, "WS2812B initialized, %d LEDs", WS2812_COUNT);
}

void ws2812_set(uint8_t idx, uint8_t r, uint8_t g, uint8_t b)
{
    if (idx >= WS2812_COUNT) return;
    led_buf[idx * 3 + 0] = g;
    led_buf[idx * 3 + 1] = r;
    led_buf[idx * 3 + 2] = b;
}

void ws2812_set_all(uint8_t r, uint8_t g, uint8_t b)
{
    for (int i = 0; i < WS2812_COUNT; i++)
        ws2812_set(i, r, g, b);
}

void ws2812_clear(void)
{
    memset(led_buf, 0, sizeof(led_buf));
}

void ws2812_show(void)
{
    rmt_transmit_config_t tx_cfg = { .loop_count = 0 };
    rmt_transmit(rmt_chan, rmt_enc, led_buf, sizeof(led_buf), &tx_cfg);
    rmt_tx_wait_all_done(rmt_chan, pdMS_TO_TICKS(100));
}
