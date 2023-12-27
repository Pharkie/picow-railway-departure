import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

#Display size
WIDTH = 128
HEIGHT = 32 

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

# Draw Some Text
text1 = "This is line 1"
text2 = "This is line 2"
text3 = "This is line 3"
(font_width, font_height) = font.getsize(text1)
draw.text((0, 1), text1, font=font, fill=255 )
draw.text((0, font_height+1), text2, font=font, fill=255 )
draw.text((0, (font_height*2)+1), text3, font=font, fill=255 )

# Display image
oled.image(image)
oled.show()
