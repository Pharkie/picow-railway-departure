import time
from machine import I2C, Pin
from lib.ssd1306 import SSD1306_I2C

# Create an I2C interface
i2c = I2C(0, scl=Pin(17), sda=Pin(16))

# Create an SSD1306 instance
oled = SSD1306_I2C(128, 32, i2c)

# Draw something on the display
oled.text("Hello, world!", 0, 12)
oled.show()

# Save the current screen contents
saved_screen_contents = bytearray(oled.buffer)

# Display a temporary message
time.sleep(2)
oled.fill(0)
oled.text("This is new", 0, 12)
oled.show()
time.sleep(2)

# Restore the saved screen contents
oled.buffer = saved_screen_contents
oled.show()
time.sleep(2)
