from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from lib.fdrawer import FontDrawer

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32

i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
oled1 = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c_oled1)

# Normal FrameBuffer operation
oled1.rect( 0, 0, 128, 32, 1 )
oled1.show()

# Use a font drawer to draw font to FrameBuffer
fd = FontDrawer(frame_buffer=oled1, font_name = 'dejav_m10' )
fd.print_str( "Font Demo", 2, 2 )
fd.print_char( "#", 100, 2 )
fd.print_str( fd.font_name, 2, 18 )

# Send the FrameBuffer content to the LCD
oled1.show()