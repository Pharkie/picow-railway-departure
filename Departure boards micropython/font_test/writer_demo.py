# writer_demo.py Demo pogram for rendering arbitrary fonts to an SSD1306 OLED display.
# Illustrates a minimal example. Requires ssd1306_setup.py which contains
# wiring details.

# The MIT License (MIT)
#
# Copyright (c) 2018 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

# VXX

from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import font_test.font6

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32

def display_text(oled, font, text, x, y):
    for char in text:
        glyph, char_height, char_width = font.get_ch(char)
        buf = bytearray(glyph)
        fbc = framebuf.FrameBuffer(buf, char_width, char_height, framebuf.MONO_HLSB)
        oled.blit(fbc, x, y)
        x += char_width

def test():
    i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
    oled1 = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c_oled1)

    oled1.fill(0)
    oled1.show()
    
    display_text(oled1, font_test.font6, "Birmingham New St", 10, 10)
    oled1.show()

test()