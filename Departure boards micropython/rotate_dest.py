from machine import Pin, I2C
import network
import utime
import ujson
import urequests
from ssd1306 import SSD1306_I2C
from wifi_creds import WIFI_SSID, WIFI_PASSWORD

WIDTH = 128
HEIGHT = 32

destinations = ["Shedditch", "Camp Hill", 'Waterdown']
next_destination = 0
future_destination = 1

next_train = 180
future_train = 610

next_time = utime.time()

i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
font_height = 11

def setup_display():
    global i2c, oled
    DISPLAY_WIDTH = 128
    DISPLAY_HEIGHT = 32

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)

    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")
        sys.exit()

    oled = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)

def calculate_next_departure(current_time, train_time, destination_index):
    next_time = current_time + train_time
    next_depart = "{:02d}:{:02d}".format(next_time // 3600, (next_time // 60) % 60)
    next_station = destinations[destination_index]
    destination_index += 1
    if destination_index >= len(destinations):
        destination_index = 0
    return next_depart, next_station, destination_index

def show_departure(y, depart_time, station):
    draw.text ((0, y), depart_time, font=font, fill=255)
    draw.text ((33, y), station, font=font, fill=255)
    draw.text ((98, y), depart_time, font=font, fill=255)

def main():
    while True:
        oled.fill(0)

        if utime.time() > next_time:
            next_time = utime.time() + next_train
            next_depart, next_station, next_destination = calculate_next_departure(utime.time(), next_train, next_destination)
            future_depart, future_station, future_destination = calculate_next_departure(utime.time(), future_train, future_destination)

        show_departure(1, next_depart, next_station)
        show_departure(12, future_depart, future_station)

        text_current_time = "{:02d}:{:02d}".format(utime.localtime()[3], utime.localtime()[4])
        (font_width, font_height) = font.getsize(text_current_time)
        draw.text ((WIDTH // 2 - font_width // 2, 23), text_current_time, font=font, fill=255)

        oled.image(image)
        oled.show()
        utime.sleep(10)

if __name__ == "__main__":
    main()