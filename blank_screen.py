import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.ssd1675 import Adafruit_SSD1675

BACKGROUND_COLOR = (255, 255, 255)
FOREGROUND_COLOR = (0, 0, 0)

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)
srcs = None


display = Adafruit_SSD1675(
    122, 250,
    spi, cs_pin=ecs,
    dc_pin=dc, sramcs_pin=srcs,
    rst_pin=rst, busy_pin=busy)
display.fill(Adafruit_EPD.WHITE)
display.rotation = 1

image = Image.new("RGB", (display.width, display.height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, display.width, display.height), fill=BACKGROUND_COLOR)
display.image(image)
display.display()
