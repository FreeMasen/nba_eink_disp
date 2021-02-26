import os
import datetime
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from . import util, models

MINUTE = 60
HOUR = 60 * MINUTE
BACKGROUND_COLOR = (255, 255, 255)
FOREGROUND_COLOR = (0, 0, 0)
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
display.rotation = 1

state = None

def _render_current(display, game: models.Game):
    image = Image.new("RGB", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height),
                    fill=BACKGROUND_COLOR)
    draw.text(
        (10, 10),
        game.home_abv(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    (away_size, teams_height) = large_font.getsize(game.away_abv())
    draw.text(
        (display.width - away_size - 10, 10),
        game.away_abv(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    draw.text(
        (10, teams_height + 15),
        game.home_score(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    (away_width, score_height) = large_font.getsize(game.away_score())
    draw.text(
        (display.width - away_width - 10, teams_height + 15),
        game.away_score(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    (clock_width, _) = small_font.getsize(game.clock or '00:00')
    draw.text(
        ((display.width // 2) - (clock_width // 2), 5),
        game.clock or '00:00',
        font=small_font,
        fill=FOREGROUND_COLOR
    )
    actions_y = teams_height + score_height + 10 + 5 + 5
    events = game.last_few_events()
    draw.text(
        (5, actions_y),
        events,
        font=small_font,
        fill=FOREGROUND_COLOR
    )

    display.image(image)
    display.display()

def _render_next(game: models.Game):
    pass

def _render_last(game: models.Game):
    pass

def _render_unknown(display):
    image = Image.new("RGB", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height),
                    fill=BACKGROUND_COLOR)
    message = 'It must be the off season...'
    (width, height) = large_font.getsize(message)
    
    draw.text(
        ((display.width // 2) - (width // 2), (display.height // 2) - (height // 2)),
        message,
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    display.image(image)
    display.display()

def render(st: models.State):
    global display
    global state
    state = st
    if state is not None:
        if state.current_game is not None:
            _render_current(display, state.current_game)
            return
        elif state.current_game is None or state.current_game.minutes_since_end() > 60 * 6:
            if state.next_game is not None:
                _render_next(display, state.next_game)
                return
            if state.next_game is not None:
                _render_last(display, state.last_game)
                return
    _render_unknown(display)
