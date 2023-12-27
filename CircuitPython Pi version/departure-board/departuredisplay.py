import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time
import datetime

#Display size
WIDTH = 128
HEIGHT = 32

# Cycle between destinations
destinations = ["Shedditch", "Camp Hill", 'Waterdown']
next_destination = 0
future_destination = 1

# Time next train (seconds)
next_train = 180
# Time future trains
future_train = 610

# set time to current time (updates in while loop)
next_time = datetime.datetime.today()

# Use for I2C.
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

# Create blank image
# image mode 1 = 1-bit colour (monochrome display).
image = Image.new("1", (oled.width, oled.height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load default font.
font = ImageFont.load_default()
font_height = 11

while (True):
    # clear image
    draw.rectangle([0,0,WIDTH,HEIGHT], fill=0)

    # Once time past then set next time
    if (datetime.datetime.today() > next_time):
        next_time = datetime.datetime.today() + datetime.timedelta(seconds=next_train)
        next_depart = next_time.strftime("%H:%M")
        future_time = next_time + datetime.timedelta(seconds=future_train)
        future_depart = future_time.strftime("%H:%M")
        next_destination += 1
        future_destination += 1
        if (next_destination >= len(destinations)):
            next_destination = 0
        if (future_destination >= len(destinations)):
            future_destination = 0
        
    
    # Line 1 = next departure
    # Departure time
    draw.text ((0, 1), next_depart, font=font, fill=255)
    next_station = destinations[next_destination]
    draw.text ((33, 1), next_station, font=font, fill=255)
    next_eta = next_depart
    draw.text ((98, 1), next_eta, font=font, fill=255)
    
    # Line 2 = future departure
    draw.text ((0, 12), future_depart, font=font, fill=255)
    future_station = destinations[future_destination]
    draw.text ((33, 12), future_station, font=font, fill=255)
    future_eta = future_depart
    draw.text ((98, 12), future_eta, font=font, fill=255)

    # Line 3 = current time (centred)
    text_current_time = time.strftime("%H:%M", time.localtime())
    (font_width, font_height) = font.getsize(text_current_time)
    draw.text ((WIDTH // 2 - font_width // 2, 23),
               text_current_time,
               font=font,
               fill=255
               )

    # Display image
    oled.image(image)
    oled.show()
    time.sleep (10)

