import os
import datetime
import time
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from . import util, models

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
display.rotation = 1

last_update = datetime.datetime(1970, 1, 1)
updating = False
state = None

def _gen_image_draw(display):
    image = Image.new("L", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height), fill=BACKGROUND_COLOR)
    return (image, draw)

def _render_current(display, game: models.Game):
    print('_render_current')
    if not game.dirty():
        return
    (image, draw) = _gen_image_draw(display)
    teams_height = _render_teams(draw, game)
    score_height = _render_score(draw, game, teams_height)
    (clock_width, _) = small_font.getsize(game.clock or '00:00')
    draw.text(
        ((display.width // 2) - (clock_width // 2), BORDER_WIDTH // 2),
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

def _render_next(display, game: models.Game):
    print('_render_next')
    (image, draw) = _gen_image_draw(display)
    teams_height = _render_teams(draw, game)
    render_centered(
        draw, medium_font, util.format_duration(game.start_time), display.width, teams_height + BORDER_WIDTH * 2
    )
    display.image(image)
    display.display()

def _render_last(display, game: models.Game):
    print('render_last')
    (image, draw) = _gen_image_draw(display)
    teams_height = _render_teams(draw, game)
    score_height = _render_score(draw, game, teams_height)
    (team, cat, bs) = game.next_box()
    if bs is None:
        print('no box score...')
        display.image(image)
        display.display()
        return
    stat_top = teams_height + score_height + (BORDER_WIDTH * 3)
    render_text = render_left_aligned
    if (team or '') == game.away_abv():
        render_text = render_right_aligned

    stat_height = render_text(draw, large_font, cat or '???', display.width, stat_top)
    value_top = BORDER_WIDTH + stat_top + stat_height
    name_value = f'{bs.name}: {bs.value}'
    render_text(draw, large_font, name_value, display.width, value_top)
    display.image(image)
    display.display()

def _render_teams(draw, game):
    draw.text(
        (BORDER_WIDTH, BORDER_WIDTH),
        game.home_abv(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    (away_size, teams_height) = large_font.getsize(game.away_abv())
    draw.text(
        (display.width - away_size - BORDER_WIDTH, BORDER_WIDTH),
        game.away_abv(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    return teams_height

def _render_score(draw, game, teams_height):
    draw.text(
        (BORDER_WIDTH, teams_height + BORDER_WIDTH * 2),
        game.home_score(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    (away_width, score_height) = large_font.getsize(game.away_score())
    draw.text(
        (display.width - away_width - BORDER_WIDTH, teams_height + BORDER_WIDTH * 2),
        game.away_score(),
        font=large_font,
        fill=FOREGROUND_COLOR
    )
    return score_height

def render_right_aligned(draw, font, text, display_width, y):
    (w, h) = font.getsize(text)
    xy = (display_width - w - BORDER_WIDTH, y)
    draw.text(
        xy,
        text,
        font=font,
        fill=FOREGROUND_COLOR
    )
    return h

def render_centered(draw, font, text, display_width, y):
    (w, h) = font.getsize(text)
    draw.text(
        ((display.width // 2) - (w // 2), y),
        text,
        font=font,
        fill=FOREGROUND_COLOR
    )
    return h

def render_left_aligned(draw, font, text, display_width, y):
    (_, h) = font.getsize(text)
    draw.text(
        (BORDER_WIDTH, y),
        text,
        font=font,
        fill=FOREGROUND_COLOR
    )
    return h

def _render_unknown(display):
    print('_render_unknown')
    (image, draw) = _gen_image_draw(display)
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
    global last_update
    global updating
    state = st
    now = datetime.datetime.now()
    secs = (now - last_update).total_seconds()
    print('eink_render', last_update, secs)
    if secs > 60 and not updating:
        updating = True
        tick()
        updating = False
        last_update = datetime.datetime.now()

def tick():
    global state
    global display
    if state is not None:
        if state.current_game is not None:
            print('minutes_since_end', state.current_game.minutes_since_end())
            if state.current_game.minutes_since_end() > 30:
                _render_last(display, state.current_game)
                return
            minutes_until_start = state.current_game.minutes_until_start()
            print('minutes_until_start', minutes_until_start)
            if minutes_until_start in range(60 * 3):
                _render_next(display, state.current_game)
                return
            if minutes_until_start <= 0:
                _render_current(display, state.current_game)
                return
        if state.last_game is not None:
            _render_last(display, state.last_game)
            return
        if state.next_game is not None:
            _render_next(display, state.next_game)
            return
    _render_unknown(display)
    time.sleep(1)