import datetime
import re
import time
import json
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)
srcs = None

from adafruit_epd.ssd1675 import Adafruit_SSD1675
display = Adafruit_SSD1675(
    122, 250,
    spi, cs_pin=ecs,
    dc_pin=dc, sramcs_pin=srcs,
    rst_pin=rst, busy_pin=busy)
display.fill(Adafruit_EPD.WHITE)
display.rotation = 1

def safe_lookup(d, key):
    try:
        return d[key]
    except KeyError:
        return None
class Team:
    def __init__(self, d):
        self.id = safe_lookup(d, "id")
        self.name = safe_lookup(d, "teamName")
        self.city = safe_lookup(d, "teamCity")
        self.abv = safe_lookup(d, "triCode")
        self.win = safe_lookup(d, "win")
        self.loss = safe_lookup(d, "loss")
        self.score = safe_lookup(d, "score")
        self.in_bonus = safe_lookup(d, "inBonus")
        self.timeouts = safe_lookup(d, "timeoutsRemaining")
        periods = safe_lookup(d, "periods")
        if isinstance(periods, list):
            self.periods = []
        
class Period:
    def __init__(self, d):
        self.score = safe_lookup(d, "score")
class Player:
    def __init__(self, d):
        self.id = safe_lookup(d, "id")
        self.name = safe_lookup(d, "name")
        self.number = safe_lookup(d, "number")
        self.position = safe_lookup(d, "position")
        self.points = safe_lookup(d, "points")
        self.rebounds = safe_lookup(d, "rebounds")
        self.assists = safe_lookup(d, "assists")

class Game:
    def __init__(self, d):
        self.start_time = safe_lookup(d, "startTime")
        self.end_time = safe_lookup(d, "endTime")
        self.clock = safe_lookup(d, "clock")
        self.period = safe_lookup(d, "period")
        self.home = safe_lookup(d, "home")
        if isinstance(self.home, dict):
            self.home = Team(self.home)
        self.away = safe_lookup(d, "away")
        if isinstance(self.away, dict):
            self.away = Team(self.away)
        self.game_leaders = safe_lookup(d, "gameLeaders")
    def start_datetime(self):
        return datetime.datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M:%S%z").astimezone(None)

def load_game():
    try:
        with open('data/today.json') as file:
            today = json.load(file)
            return Game(today)
    except:
        pass


def load_box_score():
    try:
        with open('data/box_score.json') as file:
            return json.load(file)
    except:
        pass


def load_play_by_play():
    print('load_play_by_play')
    try:
        with open('data/play_by_play.json') as file:
            return json.load(file)
    except Exception as e:
        print(f'failed to update play by play: {e}')



last_update = datetime.datetime.now()

def refresh_display(game, box_score, play_by_play):
    if game is not None:
        print(f'{game.home.abv} {game.away.abv}')
    else:
        print('HOM VIS')
    if play_by_play is not None:
        last = play_by_play[-1]
        print(f'{last["home_score"]: >3} {last["away_score"]: >3}')
        print(last["clock"])
        print(last['desc'])
    else:
        now = datetime.datetime.now().astimezone(None)
        secs = (game.start_datetime() - now).total_seconds()
        if secs < 0:
            print('Game started but no data')
        elif secs < 60:
            print(f'{int(secs)}s')
        elif secs < 60 * 60:
            print(f'{int(secs / 60)}m')
        else:
            raw_hours = secs / 60 / 60
            hours = int(raw_hours)
            minutes = int((raw_hours - hours) * 60)
            print(f'{hours}h {minutes}m')
    display.display()


game = load_game()
box_score = load_box_score()
play_by_play = load_play_by_play()
def watch_data_file():
    global game
    global box_score
    global play_by_play
    
    obs = Observer()
    handler = PatternMatchingEventHandler(['*.json'], None, False, True)
    def updated(event):
        global game
        global box_score
        global play_by_play
        if event.event_type not in ['created', 'modified']:
            return
        if 'today.json' in event.src_path:
            game = load_game()
        elif 'box_score.json' in event.src_path:
            box_score = load_box_score()
        elif 'play_by_play.json' in event.src_path:
            play_by_play = load_play_by_play()

    handler.on_any_event = updated
    obs.schedule(handler, 'data')
    obs.start()
    try:
        while True:
            refresh_display(game, box_score, play_by_play)
            time.sleep(5)
    finally:
        obs.stop()
        obs.join()
# i = inotify.adapters.Inotify()
# i.add_watch('data')

watch_data_file()

# for event in i.event_gen():
#     if event is None:
#         continue
#     else:
#         (_, type_names, path, filename) = event
#         if 'IN_CREATE' in type_names or 'IN_MODIFY' in type_names:
#             if filename.startswith('today'):
#                 game = load_game()
#             elif filename.startswith('box_score'):
#                 box_score = load_box_score()
#             elif filename.startswith('play_by_play'):
#                 play_by_play = load_play_by_play()
#     now = datetime.datetime.now()
#     if (now -  last_update).total_seconds() >= 5:
#         last_update = now
#         refresh_display()
