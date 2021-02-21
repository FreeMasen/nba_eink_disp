import datetime
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from . import util

MINUTE = 60
HOUR = 60 * MINUTE
BACKGROUND_COLOR=(255,255,255)
FOREGROUND_COLOR=(0,0,0)
import os
try:
    font_path = os.environ['NBA_EINK_FONT']
except:
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# https://www.dafont.com/lemon-milk.font
small_font = ImageFont.truetype(font_path, 8)
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

class DisplayState:
    class ProtoGame:
        def __init__(self, game):
            self.game = game

        def home_team_abv(self):
            if self.game is None:
                return 'HOM'
            return self.game.home.abv

        def away_team_abv(self):
            if self.game is None:
                return 'VIS'
            return self.game.away.abv
            
    class InGameState(ProtoGame):
        ty = 'InGame'
        def __init__(self, game, play_by_play):
            super().__init__(game)
            self.game = game
            self.play_by_play = play_by_play

        def home_team_score(self):
            if not self.has_play_by_play():
                return '  0'
            score = self.play_by_play[-1]['home_score']
            return f'{score: >3}'

        def away_team_score(self):
            if not self.has_play_by_play():
                return '  0'
            score = self.play_by_play[-1]['away_score']
            return f'{score: >3}'
        
        def clock(self):
            if not self.has_play_by_play():
                return '00:00'
            return self.play_by_play[-1]['clock']

        def last_few_events(self, ct):
            if not self.has_play_by_play():
                return ''
            return '\n'.join([p['desc'] for p in self.play_by_play[-ct:]])

        def last_event(self):
            if not self.has_play_by_play():
                return ''
            return self.play_by_play[-1]['desc']

        def has_play_by_play(self):
            return self.play_by_play is not None and len(self.play_by_play) > 0

        def render(self, display, play_by_play):
            if play_by_play is not None:
                self.play_by_play = play_by_play
            image = Image.new("RGB", (display.width, display.height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, display.width, display.height), fill=BACKGROUND_COLOR)            
            draw.text(
                (10, 10),
                self.home_team_abv(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            (away_size, teams_height) = large_font.getsize(self.away_team_abv())
            draw.text(
                (display.width - away_size - 10, 10),
                self.away_team_abv(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            draw.text(
                (10, teams_height + 15),
                self.home_team_score(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            (away_width, score_height) = large_font.getsize(self.away_team_score())
            draw.text(
                (display.width - away_width - 10, teams_height + 15),
                self.away_team_score(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            (clock_width, _) = small_font.getsize(self.clock())
            draw.text(
                ((display.width // 2) - (clock_width // 2), 5),
                self.clock(),
                font=small_font,
                fill=FOREGROUND_COLOR
            )
            actions_y = teams_height + score_height + 10 + 5 + 5
            events = ''
            for i in range(2, -1, -1):
                print(events)
                if i == 0:
                    events = ''
                    break
                events = self.last_few_events(i)
                (_, events_height) = small_font.getsize(events)
                if actions_y + events_height <= display.height:
                    break
            draw.text(
                (5, actions_y),
                events,
                font=small_font,
                fill=FOREGROUND_COLOR
            )
                
            display.image(image)
            display.display()

    class PreGameState(ProtoGame):
        ty = 'PreGame'
        def __init__(self, game):
            super().__init__(game)
            self.game = game
            if game is None:
                self._start_time = None
            else:
                self._start_time = self.game.start_datetime()

        def game_time(self):
            if self.game is None or self._start_time is None:
                return ''
            now = datetime.datetime.now().astimezone(None)
            secs = (self._start_time - now).total_seconds()
            if secs > HOUR * 6:
                return self._start_time.strftime('%m/%d/%y %h:%M')
            elif secs > HOUR:
                raw_hours = secs / 60 / 60
                hours = int(raw_hours)
                minutes = int((raw_hours - hours) * 60)
                return f'{hours}h {minutes}m'
            elif secs > MINUTE:
                return f'{int(secs / 60)}m'
            else:
                return 'game stated'

        def render(self, display, play_by_play):
            image = Image.new("RGB", (display.width, display.height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, display.width, display.height), fill=BACKGROUND_COLOR)
            draw.text(
                (10, 10),
                self.home_team_abv(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            (teams_height, away_width) = large_font.getsize(self.away_team_abv())
            draw.text(
                (display.width - away_width - 10, 10),
                self.away_team_abv(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            (_, time_width) = large_font.getsize(self.game_time())
            draw.text(
                (display.width // 2 - time_width // 2, teams_height + 10),
                self.game_time(),
                font=large_font,
                fill=FOREGROUND_COLOR
            )
            draw.text()
            display.image(image)
            display.display()

    class PostGameState(ProtoGame):
        def __init__(self, game, box_score, play_by_play):
            self.game = game
            self.box_score = box_score
            self.play_by_play = play_by_play
        
        def render(self):
            pass
        
    def __init__(self, game, box_score, play_by_play):
        if game.has_started():
            self.state = DisplayState.InGameState(game, play_by_play)
        elif game.is_over():
            self.state = DisplayState.PostGameState(game, box_score, play_by_play)
        else:
            self.state = DisplayState.PreGameState(game)

    def render(self, display, game, box_score, play_by_play):
        if self.state.ty == 'PreGame' and game.has_started():
            self.state = DisplayState.InGameState(game, play_by_play)
        elif self.state.ty == 'InGame' and game.is_over():
            self.state = DisplayState.PostGameState(game, box_score, play_by_play)
        elif not game.has_started():
            self.state = DisplayState.PreGameState(game)
        self.state.render(display, play_by_play)
    
state = None
def render(game, box_score, play_by_play):
    global state
    global display
    if game is not None:
        if state is None:
            state = DisplayState(game, box_score, play_by_play)
        state.render(display, game, box_score, play_by_play)
