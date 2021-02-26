from . import util
from typing import List, Optional

import datetime


class Team:
    def __init__(self, d):
        self.id = d.get("id", None)
        self.name = d.get("teamName", 'Home')
        self.city = d.get("teamCity", '')
        self.abv = d.get("triCode", 'HOM')
        self.win = d.get("win", 0)
        self.loss = d.get("loss", 0)
        self.score = d.get("score", 0)
        self.in_bonus = d.get("inBonus", 0)
        self.timeouts: int = d.get("timeoutsRemaining", None)
        periods = d.get("periods", [])
        if isinstance(periods, list):
            self.periods = periods
        else:
            self.periods = list()
        self.box_score = None

    def update_box_score(self, box_score: dict):
        self.box_score = BoxScore(box_score)


class Period:
    def __init__(self, d):
        self.score = d.get("score", None)


class Player:
    def __init__(self, d):
        self.id = d.get("id", None)
        self.name = d.get("name", None)
        self.number = d.get("number", None)
        self.position = d.get("position", None)
        self.points = d.get("points", None)
        self.rebounds = d.get("rebounds", None)
        self.assists = d.get("assists", None)


class BoxScoreEntry:
    def __init__(self, d: Optional[dict]):
        self.name = 'UNKNOWN_PLAYER'
        self.value = -1
        if d is None:
            return
        self.name = d.get('name', self.name)
        self.value = d.get('value', self.value)


class BoxScore:
    def __init__(self, d: dict):
        self.assists = BoxScoreEntry(d.get('assist'))
        self.blocks = BoxScoreEntry(d.get('blocks'))
        self.fouled = BoxScoreEntry(d.get('fouled'))
        self.fouler = BoxScoreEntry(d.get('fouler'))
        self.steals = BoxScoreEntry(d.get('steals'))
        self.turnovers = BoxScoreEntry(d.get('turnovers'))
        self.points = BoxScoreEntry(d.get('points'))
        self.paint_points = BoxScoreEntry(d.get('paintPoints'))
        self.threes = BoxScoreEntry(d.get('threes'))
        self.rebounds = BoxScoreEntry(d.get('rebounds'))
        self.off_rebounds = BoxScoreEntry(d.get('offRebounds'))
        self.def_rebounds = BoxScoreEntry(d.get('defRebounds'))
        self._current_value = 'Assists'

    def next(self) -> (str, BoxScoreEntry):
        '''
        Returns the name and BoxScoreEntry for each box score value captured
        '''
        name = self._current_value
        if self._current_value == 'Assists':
            self._current_value = 'Blocks'
            ent = self.assists
        if self._current_value == 'Blocks':
            self._current_value = 'Fouled'
            ent = self.blocks
        if self._current_value == 'Fouled':
            self._current_value = 'Fouler'
            ent = self.fouled
        if self._current_value == 'Fouler':
            self._current_value = 'Steals'
            ent = self.fouler
        if self._current_value == 'Steals':
            self._current_value = 'Turnovers'
            ent = self.steals
        if self._current_value == 'Turnovers':
            self._current_value = 'Points'
            ent = self.turnovers
        if self._current_value == 'Points':
            self._current_value = 'Paint Points'
            ent = self.points
        if self._current_value == 'Paint Points':
            self._current_value = 'Threes'
            ent = self.paint_points
        if self._current_value == 'Threes':
            self._current_value = 'Rebounds'
            ent = self.threes
        if self._current_value == 'Rebounds':
            self._current_value = 'Off Rebounds'
            ent = self.rebounds
        if self._current_value == 'Off Rebounds':
            self._current_value = 'Def Rebounds'
            ent = self.off_rebounds
        else:
            self._current_value = 'Assists'
            ent = self.def_rebounds
        return (name, ent)


class Game:
    def __init__(self, d: dict, raw_play_by_play: List[dict] = list(), box_score: dict = dict()):
        self._dirty = True
        self.id = d.get('id', 'UNKNOWN_GAME_ID')
        _start_time = d.get('startTime', None)
        if _start_time is not None:
            self.start_time = util.parse_datetime(_start_time)
        else:
            self.start_time = None

        _end_time = d.get("endTime", None)
        if _end_time is not None:
            self.end_time = util.parse_datetime(_end_time)
        else:
            self.end_time = None

        self.clock = d.get("clock", None)
        self.period = d.get("period", None)
        _home = d.get("home", None)
        if isinstance(_home, dict):
            self.home = Team(_home)
        else:
            self.home = None

        _away = d.get("away", None)
        if isinstance(_away, dict):
            self.away = Team(_away)
        else:
            self.away = None

        self.game_leaders = d.get("gameLeaders", None)
        if raw_play_by_play is not None:
            self.play_by_play = [Play(p) for p in raw_play_by_play]
        else:
            self.play_by_play = list()

        if len(self.play_by_play) > 0:
            self._last_play_by_play = self.play_by_play[-1].number
        else:
            self._last_play_by_play = -1

    def update(self, game: Optional[dict], raw_play_by_play: Optional[List[dict]]):
        if game is not None:
            if game.end_time is None:
                end_str = game.get('endTime')
                if end_str is not None:
                    end_time = util.parse_datetime(end_str)
                    self._dirty = self._dirty or self.end_time != end_time
                    self.end_time = util.parse_datetime(end_str)
            clock = game.get('clock', self.clock)
            self._dirty = self.clock != clock
            self.clock = self._dirty or clock
            period = game.get('period', self.period)
            self._dirty = self._dirty or self.period != period
            self.period = period
        if raw_play_by_play is not None:
            self.update_play_by_play(raw_play_by_play)

    def update_play_by_play(self, raw_play_by_play: List[dict]):
        for entry in raw_play_by_play:
            n = entry.get('number', -1)
            if n > self._last_play_by_play:
                self._dirty = True
                self._last_play_by_play = n
                self.play_by_play.append(Play(entry))

    def update_box_score(self, box_score: dict):
        self.box_score = BoxScore(box_score)

    def home_abv(self) -> str:
        if self.home is None:
            return 'HOM'
        return self.home.abv or 'HOM'

    def home_score(self) -> int:
        if len(self.play_by_play) > 0:
            return f'{self.play_by_play[-1].home_score}'
        if self.home is None:
            return '0'
        return f'{self.home.score}'

    def away_score(self) -> int:
        if len(self.play_by_play) > 0:
            return f'{self.play_by_play[-1].away_score}'
        if self.away is None:
            return '0'
        return f'{self.away.score}'

    def away_abv(self) -> str:
        if self.away is None:
            return 'VIS'
        return self.away.abv or 'VIS'

    def start_datetime(self) -> datetime.datetime:
        if self.start_time is None:
            return datetime.datetime(3000, 1, 1).astimezone(None)
        return self.start_time

    def has_started(self) -> bool:
        now = datetime.datetime.now().astimezone(None)
        return (self.start_datetime() - now).total_seconds() <= 0

    def is_over(self) -> bool:
        return self.end_time is not None

    def minutes_since_end(self) -> int:
        if self.end_time is None:
            return -1
        now = datetime.datetime.now().astimezone(None)
        return int((self.end_time - now).total_seconds() / 60)

    def last_few_events(self) -> str:
        if len(self.play_by_play) <= 0:
            return ''
        return '\n'.join([p.desc for p in self.play_by_play[-3:]])

    def dirty(self) -> bool:
        ret = self._dirty
        self._dirty = False
        return ret

class Play:
    def __init__(self, d):
        self.number = util.safe_lookup(d, 'number')
        self.type = util.safe_lookup(d, 'type')
        self.clock = util.safe_lookup(d, 'clock')
        self.desc = util.safe_lookup(d, 'desc')
        self.home_score = util.safe_lookup(d, 'home_score')
        self.away_score = util.safe_lookup(d, 'away_score')
        self.quarter = util.safe_lookup(d, 'quarter')


class State:
    def __init__(self,
                 current_game: Optional[dict],
                 play_by_play: Optional[List[dict]],
                 next_game: Optional[dict],
                 last_game: Optional[dict],
                 box_score: Optional[dict],
                 ):
        if current_game is not None:
            self.current_game = Game(
                current_game, raw_play_by_play=play_by_play)
        if next_game is not None:
            self.next_game = Game(next_game)
        if last_game is not None:
            self.last_game = Game(last_game, box_score=box_score)

    def update_current(self, game: Optional[dict], play_by_play: Optional[List[dict]]):
        if self.current_game is None and game is None:
            return
        if self.current_game is None:
            self.current_game = game
        if play_by_play is not None:
            self.current_game.update(game, play_by_play)

    def update_next(self, next: dict):
        self.next_game = Game(next)

    def update_last(self, last: dict, box_score: dict):
        if self.last_game is None:
            if last is None:
                self.last_game = Game(last, box_score=box_score)
            elif self.last_game.id != last.get('id', 'NEXT_GAME_ID'):
                self.last_game = Game(last, box_score=box_score)
            else:
                self.last_game.update_box_score(box_score)
