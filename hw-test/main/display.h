#pragma once
#include <stdint.h>
#include "badge_hw.h"

void display_init(void);
void display_fill(uint16_t color);
void display_fill_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
void display_draw_pixel(int16_t x, int16_t y, uint16_t color);
void display_draw_char(int16_t x, int16_t y, char c, uint16_t fg, uint16_t bg, uint8_t scale);
void display_draw_string(int16_t x, int16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t scale);
void display_draw_string_center(int16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t scale);
void display_draw_hline(int16_t x, int16_t y, int16_t w, uint16_t color);
void display_draw_vline(int16_t x, int16_t y, int16_t h, uint16_t color);
void display_draw_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
void display_fill_circle(int16_t cx, int16_t cy, int16_t r, uint16_t color);
