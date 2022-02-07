import os
from typing import List
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.ssd1675 import Adafruit_SSD1675

MINUTE = 60
HOUR = 60 * MINUTE
BACKGROUND_COLOR = 255
FOREGROUND_COLOR = 1
BORDER_WIDTH = 5

try:
    font_path = os.environ['NBA_EINK_FONT']
except:
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# https://www.dafont.com/lemon-milk.font
small_font = ImageFont.truetype(font_path, 12)
medium_font = ImageFont.truetype(font_path, 16)
large_font = ImageFont.truetype(font_path, 24)

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
display.rotation = 3

def _gen_image_draw(display):
    image = Image.new("L", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height), fill=BACKGROUND_COLOR)
    return (image, draw)

def render(lines: List[str]):
    global display
    (image, draw) = _gen_image_draw(display)
    top = 5
    for line in lines:
        char_ct = len(line)
        if char_ct == 0:
            continue

        size = line[0]
        if size == '1':
            font = medium_font
        elif size == '2':
            font = large_font
        else:
            # assume 0
            font = small_font
        msg = line[1:]
        (width, height) = font.getsize(msg)
        if char_ct == 1:
            top += height + 5
            continue
        draw.text(
            ((display.width // 2) - (width // 2), top),
            msg,
            font=font,
            fill=FOREGROUND_COLOR
        )
        top += height
    display.image(image)
    display.display()
