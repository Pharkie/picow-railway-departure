# ssd1306_setup.py Demo pogram for rendering arbitrary fonts to an SSD1306 OLED display.
# Device initialisation

# The MIT License (MIT)
#
# Copyright (c) 2016 Peter Hinch
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

# V0.3 12th Aug 2018

from machine import Pin, I2C
from ssd1306 import SSD1306_SPI, SSD1306_I2C

WIDTH = const(128)
HEIGHT = const(32)

def setup(use_spi=False, soft=True):
    if use_spi:
        # Pyb   SSD
        # 3v3   Vin
        # Gnd   Gnd
        # X1    DC
        # X2    CS
        # X3    Rst
        # X6    CLK
        # X8    DATA
        pdc = Pin('X1', Pin.OUT_PP)
        pcs = Pin('X2', Pin.OUT_PP)
        prst = Pin('X3', Pin.OUT_PP)
        if soft:
            spi = SPI(sck=Pin('X6'), mosi=Pin('X8'), miso=Pin('X7'))
        else:
            spi = SPI(1)
        ssd = SSD1306_SPI(WIDTH, HEIGHT, spi, pdc, prst, pcs)
    else:  # I2C
        # Pyb   SSD
        # 3v3   Vin
        # Gnd   Gnd
        # Y9    CLK
        # Y10   DATA
        if soft:
            # pscl = Pin(Pin(17), Pin.OPEN_DRAIN)
            # psda = Pin(Pin(19), Pin.OPEN_DRAIN)
            # i2c = I2C(scl=pscl, sda=psda)
            i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
        else:
            i2c = I2C(2)
        ssd = SSD1306_I2C(WIDTH, HEIGHT, i2c)
    return ssd