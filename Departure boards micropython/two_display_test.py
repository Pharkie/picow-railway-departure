from machine import Pin, I2C
import utime
import uasyncio as asyncio
import time
import datetime_utils
import utils
import rail_data
import urandom
from ssd1306 import SSD1306_I2C
from config import LINEONE_Y, LINETWO_Y, LINETHREE_Y, DISPLAY_WIDTH, DISPLAY_HEIGHT, LINE_HEIGHT, CHAR_WIDTH, offline_mode
import main

async def scroll_text(oled, text, y, speed=5): # Speed is 1-5, 1 being slowest
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * CHAR_WIDTH
    step_size = 6
    # wait_secs = 0.2 + (speed - 1) * (0.05 - 0.2) / (5 - 1)
  
    for x in range(DISPLAY_WIDTH, -(text_width+step_size), -step_size): # -8 because each character is 8 pixels wide. Smoother scrolling takes too much CPU.
        main.clear_line(oled, y)
        oled.text(text, x, y) 
        oled.show()

        await asyncio.sleep(0.1)  # Delay between frames

async def test(oled1, oled2):
    test_string = "Departing from London (12:30) -> Birmingham (14:00) -> Manchester (15:30) -> Leeds (17:00) -> Newcastle (18:30) -> Edinburgh (20:00)"

    while True:
        await asyncio.gather(
            scroll_text(oled1, test_string, LINETWO_Y),
            scroll_text(oled2, test_string, LINETWO_Y)
        )

if __name__ == "__main__":
    oled1, oled2 = main.setup_displays()

    main.clear_display(oled1)
    main.clear_display(oled2)

    asyncio.run(test(oled1, oled2))