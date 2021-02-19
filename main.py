import datetime
import re
import time
import json
import inotify.adapters

WOLVES_ID = 1610612750
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
    try:
        with open('data/play_by_play.json') as file:
            return json.load(file)
    except:
        pass


game = load_game()
box_score = load_box_score()
play_by_play = load_play_by_play()
last_update = datetime.datetime.now()

def refresh_display():
    if game is not None:
        print(f'{game.home.abv} {game.away.abv}')
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
    else:
        print('no game data')


refresh_display()
i = inotify.adapters.Inotify()
i.add_watch('data')


for event in i.event_gen():
    if event is None:
        continue
    else:
        (_, type_names, path, filename) = event
        if 'IN_CREATE' in type_names or 'IN_MODIFY' in type_names:
            if filename.startswith('today'):
                game = load_game()
            elif filename.startswith('box_score'):
                box_score = load_box_score()
            elif filename.startswith('play_by_play'):
                play_by_play = load_play_by_play()
    now = datetime.datetime.now()
    if (now -  last_update).total_seconds() >= 5:
        last_update = now
        refresh_display()
