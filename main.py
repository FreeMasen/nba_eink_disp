import datetime
import re
import time
import json

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

with open('data/today.json') as file:
    today = json.load(file)
    game = Game(today)

while True:
    with open('data/play_by_play.json') as file: 
        actions = json.load(file)
        last = actions[-1]
        print(last["clock"])
        print(f'{game.home.abv} {game.away.abv}')
        print(f'{last["home_score"]: >3} {last["away_score"]: >3}')
        print(last['desc'])
    time.sleep(5)

# def data_type(v):
#     if isinstance(v, list):
#         return '|'.join([data_type(x) for x in v]) + '[]'
#     return type(v).__name__

# import os
# uniques = dict()
# for root, _d, files in os.walk('exp'):
#     for file in files:
#         if file.startswith('play'):
#             with open(os.path.join(root, file)) as f:
#                 d = json.load(f)
#                 game = d['game']
#                 acts = game['actions']
#                 for act in acts:
#                     ty = act['actionType']
#                     curr = safe_lookup(uniques, ty)
#                     if curr is None:
#                         curr = dict()
#                     ct = safe_lookup(curr, '__total_count')
#                     if ct is None:
#                         ct = 0
#                     ct += 1
#                     curr['__total_count'] = ct
#                     for key, value in act.items():
#                         data = safe_lookup(curr, key)
#                         if data is None:
#                             data = dict()
#                         ct = safe_lookup(data, 'count')
#                         if ct is None:
#                             ct = 0
#                         ct += 1
#                         data['count'] = ct
#                         tys = safe_lookup(data, 'types')
#                         if tys is None:
#                             tys = []
#                         e_ty = data_type(value)
#                         if e_ty not in tys:
#                             tys.append(e_ty)
#                         data['types'] = tys
#                         curr[key] = data   
#                     # curr.append(act)
#                     uniques[ty] = curr
# print(json.dumps(uniques))
