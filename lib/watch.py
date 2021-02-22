import datetime
import time
import json
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


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
        self.start_time = None
        self.end_time = None
        self.clock = None
        self.period = None
        self.home = None
        self.away = None
        self.game_leaders = None
        self.update(d)

    def update(self, d):
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

    def has_started(self):
        now = datetime.datetime.now().astimezone(None)
        return (self.start_datetime() - now).total_seconds() <= 0

    def is_over(self):
        return self.end_time is not None
    
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
    try:
        with open('data/play_by_play.json') as file:
            return json.load(file)
    except Exception as e:
        print(f'failed to update play by play: {e}')

game = load_game()
box_score = load_box_score()
play_by_play = load_play_by_play()

def watch_data_file(data_dir, cb, lazy_refresh):
    global game
    global box_score
    global play_by_play
    cb(game, box_score, play_by_play)
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
        if not lazy_refresh:
            cb(game, box_score, play_by_play)
    
    handler.on_any_event = updated
    obs.schedule(handler, data_dir)
    obs.start()
    try:
        while True:
            if lazy_refresh:
                cb(game, box_score, play_by_play)
            time.sleep(60 * 3)
    finally:
        obs.stop()
        obs.join()

def start(data_dir, cb, lazy_refresh):
    watch_data_file(data_dir, cb, lazy_refresh)
