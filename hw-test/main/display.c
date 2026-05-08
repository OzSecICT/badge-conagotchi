#include <string.h>
#include <stddef.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "display.h"

static const char *TAG = "display";
static spi_device_handle_t spi_dev;

/* 5x7 font, ASCII 32-127 */
static const uint8_t font5x7[][5] = {
    {0x00,0x00,0x00,0x00,0x00}, /* ' ' */
    {0x00,0x00,0x5F,0x00,0x00}, /* '!' */
    {0x00,0x07,0x00,0x07,0x00}, /* '"' */
    {0x14,0x7F,0x14,0x7F,0x14}, /* '#' */
    {0x24,0x2A,0x7F,0x2A,0x12}, /* '$' */
    {0x23,0x13,0x08,0x64,0x62}, /* '%' */
    {0x36,0x49,0x55,0x22,0x50}, /* '&' */
    {0x00,0x05,0x03,0x00,0x00}, /* ''' */
    {0x00,0x1C,0x22,0x41,0x00}, /* '(' */
    {0x00,0x41,0x22,0x1C,0x00}, /* ')' */
    {0x14,0x08,0x3E,0x08,0x14}, /* '*' */
    {0x08,0x08,0x3E,0x08,0x08}, /* '+' */
    {0x00,0x50,0x30,0x00,0x00}, /* ',' */
    {0x08,0x08,0x08,0x08,0x08}, /* '-' */
    {0x00,0x60,0x60,0x00,0x00}, /* '.' */
    {0x20,0x10,0x08,0x04,0x02}, /* '/' */
    {0x3E,0x51,0x49,0x45,0x3E}, /* '0' */
    {0x00,0x42,0x7F,0x40,0x00}, /* '1' */
    {0x42,0x61,0x51,0x49,0x46}, /* '2' */
    {0x21,0x41,0x45,0x4B,0x31}, /* '3' */
    {0x18,0x14,0x12,0x7F,0x10}, /* '4' */
    {0x27,0x45,0x45,0x45,0x39}, /* '5' */
    {0x3C,0x4A,0x49,0x49,0x30}, /* '6' */
    {0x01,0x71,0x09,0x05,0x03}, /* '7' */
    {0x36,0x49,0x49,0x49,0x36}, /* '8' */
    {0x06,0x49,0x49,0x29,0x1E}, /* '9' */
    {0x00,0x36,0x36,0x00,0x00}, /* ':' */
    {0x00,0x56,0x36,0x00,0x00}, /* ';' */
    {0x08,0x14,0x22,0x41,0x00}, /* '<' */
    {0x14,0x14,0x14,0x14,0x14}, /* '=' */
    {0x00,0x41,0x22,0x14,0x08}, /* '>' */
    {0x02,0x01,0x51,0x09,0x06}, /* '?' */
    {0x32,0x49,0x79,0x41,0x3E}, /* '@' */
    {0x7E,0x11,0x11,0x11,0x7E}, /* 'A' */
    {0x7F,0x49,0x49,0x49,0x36}, /* 'B' */
    {0x3E,0x41,0x41,0x41,0x22}, /* 'C' */
    {0x7F,0x41,0x41,0x22,0x1C}, /* 'D' */
    {0x7F,0x49,0x49,0x49,0x41}, /* 'E' */
    {0x7F,0x09,0x09,0x09,0x01}, /* 'F' */
    {0x3E,0x41,0x49,0x49,0x7A}, /* 'G' */
    {0x7F,0x08,0x08,0x08,0x7F}, /* 'H' */
    {0x00,0x41,0x7F,0x41,0x00}, /* 'I' */
    {0x20,0x40,0x41,0x3F,0x01}, /* 'J' */
    {0x7F,0x08,0x14,0x22,0x41}, /* 'K' */
    {0x7F,0x40,0x40,0x40,0x40}, /* 'L' */
    {0x7F,0x02,0x0C,0x02,0x7F}, /* 'M' */
    {0x7F,0x04,0x08,0x10,0x7F}, /* 'N' */
    {0x3E,0x41,0x41,0x41,0x3E}, /* 'O' */
    {0x7F,0x09,0x09,0x09,0x06}, /* 'P' */
    {0x3E,0x41,0x51,0x21,0x5E}, /* 'Q' */
    {0x7F,0x09,0x19,0x29,0x46}, /* 'R' */
    {0x46,0x49,0x49,0x49,0x31}, /* 'S' */
    {0x01,0x01,0x7F,0x01,0x01}, /* 'T' */
    {0x3F,0x40,0x40,0x40,0x3F}, /* 'U' */
    {0x1F,0x20,0x40,0x20,0x1F}, /* 'V' */
    {0x3F,0x40,0x38,0x40,0x3F}, /* 'W' */
    {0x63,0x14,0x08,0x14,0x63}, /* 'X' */
    {0x07,0x08,0x70,0x08,0x07}, /* 'Y' */
    {0x61,0x51,0x49,0x45,0x43}, /* 'Z' */
    {0x00,0x7F,0x41,0x41,0x00}, /* '[' */
    {0x02,0x04,0x08,0x10,0x20}, /* '\' */
    {0x00,0x41,0x41,0x7F,0x00}, /* ']' */
    {0x04,0x02,0x01,0x02,0x04}, /* '^' */
    {0x40,0x40,0x40,0x40,0x40}, /* '_' */
    {0x00,0x01,0x02,0x04,0x00}, /* '`' */
    {0x20,0x54,0x54,0x54,0x78}, /* 'a' */
    {0x7F,0x48,0x44,0x44,0x38}, /* 'b' */
    {0x38,0x44,0x44,0x44,0x20}, /* 'c' */
    {0x38,0x44,0x44,0x48,0x7F}, /* 'd' */
    {0x38,0x54,0x54,0x54,0x18}, /* 'e' */
    {0x08,0x7E,0x09,0x01,0x02}, /* 'f' */
    {0x0C,0x52,0x52,0x52,0x3E}, /* 'g' */
    {0x7F,0x08,0x04,0x04,0x78}, /* 'h' */
    {0x00,0x44,0x7D,0x40,0x00}, /* 'i' */
    {0x20,0x40,0x44,0x3D,0x00}, /* 'j' */
    {0x7F,0x10,0x28,0x44,0x00}, /* 'k' */
    {0x00,0x41,0x7F,0x40,0x00}, /* 'l' */
    {0x7C,0x04,0x18,0x04,0x78}, /* 'm' */
    {0x7C,0x08,0x04,0x04,0x78}, /* 'n' */
    {0x38,0x44,0x44,0x44,0x38}, /* 'o' */
    {0x7C,0x14,0x14,0x14,0x08}, /* 'p' */
    {0x08,0x14,0x14,0x18,0x7C}, /* 'q' */
    {0x7C,0x08,0x04,0x04,0x08}, /* 'r' */
    {0x48,0x54,0x54,0x54,0x20}, /* 's' */
    {0x04,0x3F,0x44,0x40,0x20}, /* 't' */
    {0x3C,0x40,0x40,0x20,0x7C}, /* 'u' */
    {0x1C,0x20,0x40,0x20,0x1C}, /* 'v' */
    {0x3C,0x40,0x30,0x40,0x3C}, /* 'w' */
    {0x44,0x28,0x10,0x28,0x44}, /* 'x' */
    {0x0C,0x50,0x50,0x50,0x3C}, /* 'y' */
    {0x44,0x64,0x54,0x4C,0x44}, /* 'z' */
    {0x00,0x08,0x36,0x41,0x00}, /* '{' */
    {0x00,0x00,0x7F,0x00,0x00}, /* '|' */
    {0x00,0x41,0x36,0x08,0x00}, /* '}' */
    {0x10,0x08,0x08,0x10,0x08}, /* '~' */
};

/* GC9A01 commands */
#define GC9A01_SWRESET  0x01
#define GC9A01_SLPOUT   0x11
#define GC9A01_INVON    0x21
#define GC9A01_DISPON   0x29
#define GC9A01_CASET    0x2A
#define GC9A01_RASET    0x2B
#define GC9A01_RAMWR    0x2C

static void dc_cmd(void)  { gpio_set_level(DISP_DC_PIN, 0); }
static void dc_data(void) { gpio_set_level(DISP_DC_PIN, 1); }

static void spi_write_byte(uint8_t b)
{
    spi_transaction_t t = {
        .length = 8,
        .tx_buffer = &b,
    };
    spi_device_polling_transmit(spi_dev, &t);
}

static void spi_write_buf(const uint8_t *buf, size_t len)
{
    if (len == 0) return;
    spi_transaction_t t = {
        .length = len * 8,
        .tx_buffer = buf,
    };
    spi_device_polling_transmit(spi_dev, &t);
}

static void write_cmd(uint8_t cmd)
{
    dc_cmd();
    spi_write_byte(cmd);
}

static void write_data(uint8_t data)
{
    dc_data();
    spi_write_byte(data);
}

static void gc9a01_init_sequence(void)
{
    /* Hardware reset */
    gpio_set_level(DISP_RST_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(DISP_RST_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(120));

    write_cmd(0xEF);
    write_cmd(0xEB); write_data(0x14);
    write_cmd(0xFE);
    write_cmd(0xEF);
    write_cmd(0xEB); write_data(0x14);
    write_cmd(0x84); write_data(0x40);
    write_cmd(0x85); write_data(0xFF);
    write_cmd(0x86); write_data(0xFF);
    write_cmd(0x87); write_data(0xFF);
    write_cmd(0x88); write_data(0x0A);
    write_cmd(0x89); write_data(0x21);
    write_cmd(0x8A); write_data(0x00);
    write_cmd(0x8B); write_data(0x80);
    write_cmd(0x8C); write_data(0x01);
    write_cmd(0x8D); write_data(0x01);
    write_cmd(0x8E); write_data(0xFF);
    write_cmd(0x8F); write_data(0xFF);
    write_cmd(0xB6); write_data(0x00); write_data(0x00);
    write_cmd(0x36); write_data(0x48);
    write_cmd(0x3A); write_data(0x05); /* RGB565 */
    write_cmd(0x90); write_data(0x08); write_data(0x08); write_data(0x08); write_data(0x08);
    write_cmd(0xBD); write_data(0x06);
    write_cmd(0xBC); write_data(0x00);
    write_cmd(0xFF); write_data(0x60); write_data(0x01); write_data(0x04);
    write_cmd(0xC3); write_data(0x13);
    write_cmd(0xC4); write_data(0x13);
    write_cmd(0xC9); write_data(0x22);
    write_cmd(0xBE); write_data(0x11);
    write_cmd(0xE1); write_data(0x10); write_data(0x0E);
    write_cmd(0xDF); write_data(0x21); write_data(0x0C); write_data(0x02);
    write_cmd(0xF0); write_data(0x45); write_data(0x09); write_data(0x08);
                     write_data(0x08); write_data(0x26); write_data(0x2A);
    write_cmd(0xF1); write_data(0x43); write_data(0x70); write_data(0x72);
                     write_data(0x36); write_data(0x37); write_data(0x6F);
    write_cmd(0xF2); write_data(0x45); write_data(0x09); write_data(0x08);
                     write_data(0x08); write_data(0x26); write_data(0x2A);
    write_cmd(0xF3); write_data(0x43); write_data(0x70); write_data(0x72);
                     write_data(0x36); write_data(0x37); write_data(0x6F);
    write_cmd(0xED); write_data(0x1B); write_data(0x0B);
    write_cmd(0xAE); write_data(0x77);
    write_cmd(0xCD); write_data(0x63);
    write_cmd(0x70); write_data(0x07); write_data(0x07); write_data(0x04);
                     write_data(0x0E); write_data(0x0F); write_data(0x09);
                     write_data(0x07); write_data(0x08); write_data(0x03);
    write_cmd(0xE8); write_data(0x34);
    write_cmd(0x62); write_data(0x18); write_data(0x0D); write_data(0x71);
                     write_data(0xED); write_data(0x70); write_data(0x70);
                     write_data(0x18); write_data(0x0F); write_data(0x71);
                     write_data(0xEF); write_data(0x70); write_data(0x70);
    write_cmd(0x63); write_data(0x18); write_data(0x11); write_data(0x71);
                     write_data(0xF1); write_data(0x70); write_data(0x70);
                     write_data(0x18); write_data(0x13); write_data(0x71);
                     write_data(0xF3); write_data(0x70); write_data(0x70);
    write_cmd(0x64); write_data(0x28); write_data(0x29); write_data(0xF1);
                     write_data(0x01); write_data(0xF1); write_data(0x00);
                     write_data(0x07);
    write_cmd(0x66); write_data(0x3C); write_data(0x00); write_data(0xCD);
                     write_data(0x67); write_data(0x45); write_data(0x45);
                     write_data(0x10); write_data(0x00); write_data(0x00);
                     write_data(0x00);
    write_cmd(0x67); write_data(0x00); write_data(0x3C); write_data(0x00);
                     write_data(0x00); write_data(0x00); write_data(0x01);
                     write_data(0x54); write_data(0x10); write_data(0x32);
                     write_data(0x98);
    write_cmd(0x74); write_data(0x10); write_data(0x85); write_data(0x80);
                     write_data(0x00); write_data(0x00); write_data(0x4E);
                     write_data(0x00);
    write_cmd(0x98); write_data(0x3E); write_data(0x07);
    write_cmd(GC9A01_INVON);
    write_cmd(GC9A01_SLPOUT);
    vTaskDelay(pdMS_TO_TICKS(120));
    write_cmd(GC9A01_DISPON);
    vTaskDelay(pdMS_TO_TICKS(20));
}

static void set_addr_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1)
{
    write_cmd(GC9A01_CASET);
    dc_data();
    uint8_t xdata[] = {x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF};
    spi_write_buf(xdata, 4);

    write_cmd(GC9A01_RASET);
    dc_data();
    uint8_t ydata[] = {y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF};
    spi_write_buf(ydata, 4);

    write_cmd(GC9A01_RAMWR);
    dc_data();
}

void display_init(void)
{
    gpio_config_t io = {
        .pin_bit_mask = (1ULL << DISP_DC_PIN) | (1ULL << DISP_RST_PIN),
        .mode = GPIO_MODE_OUTPUT,
    };
    gpio_config(&io);

    spi_bus_config_t buscfg = {
        .mosi_io_num = DISP_MOSI_PIN,
        .miso_io_num = -1,
        .sclk_io_num = DISP_SCK_PIN,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = DISP_WIDTH * DISP_HEIGHT * 2,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(DISP_SPI_HOST, &buscfg, SPI_DMA_CH_AUTO));

    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = DISP_SPI_FREQ,
        .mode = 0,
        .spics_io_num = DISP_CS_PIN,
        .queue_size = 7,
    };
    ESP_ERROR_CHECK(spi_bus_add_device(DISP_SPI_HOST, &devcfg, &spi_dev));

    gc9a01_init_sequence();
    ESP_LOGI(TAG, "GC9A01 initialized");
}

void display_fill(uint16_t color)
{
    display_fill_rect(0, 0, DISP_WIDTH, DISP_HEIGHT, color);
}

void display_fill_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color)
{
    if (x >= DISP_WIDTH || y >= DISP_HEIGHT || w <= 0 || h <= 0) return;
    if (x + w > DISP_WIDTH)  w = DISP_WIDTH  - x;
    if (y + h > DISP_HEIGHT) h = DISP_HEIGHT - y;

    set_addr_window(x, y, x + w - 1, y + h - 1);

    uint8_t hi = color >> 8, lo = color & 0xFF;
    /* Send row by row using a line buffer */
    static uint8_t line[DISP_WIDTH * 2];
    for (int i = 0; i < w; i++) {
        line[i * 2]     = hi;
        line[i * 2 + 1] = lo;
    }
    for (int row = 0; row < h; row++) {
        spi_write_buf(line, w * 2);
    }
}

void display_draw_pixel(int16_t x, int16_t y, uint16_t color)
{
    if (x < 0 || x >= DISP_WIDTH || y < 0 || y >= DISP_HEIGHT) return;
    set_addr_window(x, y, x, y);
    uint8_t buf[2] = {color >> 8, color & 0xFF};
    spi_write_buf(buf, 2);
}

void display_draw_hline(int16_t x, int16_t y, int16_t w, uint16_t color)
{
    display_fill_rect(x, y, w, 1, color);
}

void display_draw_vline(int16_t x, int16_t y, int16_t h, uint16_t color)
{
    display_fill_rect(x, y, 1, h, color);
}

void display_draw_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color)
{
    display_draw_hline(x, y, w, color);
    display_draw_hline(x, y + h - 1, w, color);
    display_draw_vline(x, y, h, color);
    display_draw_vline(x + w - 1, y, h, color);
}

void display_draw_char(int16_t x, int16_t y, char c, uint16_t fg, uint16_t bg, uint8_t scale)
{
    if (c < 32 || c > 126) c = '?';
    const uint8_t *glyph = font5x7[c - 32];
    for (int col = 0; col < 5; col++) {
        uint8_t line = glyph[col];
        for (int row = 0; row < 7; row++) {
            uint16_t color = (line & (1 << row)) ? fg : bg;
            if (scale == 1) {
                display_draw_pixel(x + col, y + row, color);
            } else {
                display_fill_rect(x + col * scale, y + row * scale, scale, scale, color);
            }
        }
    }
}

void display_draw_string(int16_t x, int16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t scale)
{
    int16_t cx = x;
    while (*str) {
        display_draw_char(cx, y, *str++, fg, bg, scale);
        cx += 6 * scale;
    }
}

void display_draw_string_center(int16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t scale)
{
    size_t len = 0;
    const char *p = str;
    while (*p++) len++;
    int16_t x = (DISP_WIDTH - (int16_t)(len * 6 * scale)) / 2;
    if (x < 0) x = 0;
    display_draw_string(x, y, str, fg, bg, scale);
}

/* Integer square root — avoids math.h dependency */
static int16_t isqrt16(int32_t n)
{
    if (n <= 0) return 0;
    int32_t x = n, y = (x + 1) / 2;
    while (y < x) { x = y; y = (x + n / x) / 2; }
    return (int16_t)x;
}

void display_fill_circle(int16_t cx, int16_t cy, int16_t r, uint16_t color)
{
    for (int16_t dy = -r; dy <= r; dy++) {
        int16_t dx = isqrt16(r * r - dy * dy);
        display_fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color);
    }
}
