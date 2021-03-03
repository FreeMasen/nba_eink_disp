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
    values = [
        'Assists',
        'Blocks',
        'Fouled',
        'Fouler',
        'Steals',
        'Turnovers',
        'Points',
        'Paint Points',
        'Threes',
        'Rebounds',
        'Off Rebounds',
        'Def Rebounds',
    ]

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
        self._current_value = 0

    def len(self):
        return 12

    def next(self) -> (str, BoxScoreEntry):
        '''
        Returns the name and BoxScoreEntry for each box score value captured
        '''
        name = BoxScore.values[self._current_value]
        if self._current_value == 0:
            ent = self.assists
        elif self._current_value == 1:
            ent = self.blocks
        elif self._current_value == 2:
            ent = self.fouled
        elif self._current_value == 3:
            ent = self.fouler
        elif self._current_value == 4:
            ent = self.steals
        elif self._current_value == 5:
            ent = self.turnovers
        elif self._current_value == 6:
            ent = self.points
        elif self._current_value == 7:
            ent = self.paint_points
        elif self._current_value == 8:
            ent = self.threes
        elif self._current_value == 9:
            ent = self.rebounds
        elif self._current_value == 10:
            ent = self.off_rebounds
        else:
            ent = self.def_rebounds
        self._current_value += 1
        if self._current_value >= len(BoxScore.values):
            self._current_value = 0
        return (name, ent)


class Game:
    def __init__(self, d: dict, raw_play_by_play: List[dict] = list(), box_score: dict = dict()):
        self._dirty = True
        self._bs_home = True
        d = d or dict()
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
            _bs = (box_score or dict()).get(
                'home', dict()).get('boxScore', None)
            if _bs is not None:
                self.home.update_box_score(_bs)
        else:
            self.home = None

        _away = d.get("away", None)
        if isinstance(_away, dict):
            self.away = Team(_away)
            _bs = (box_score or dict()).get(
                'away', dict()).get('boxScore', None)
            if _bs is not None:
                self.away.update_box_score(_bs)
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
        self.minutes_until_start() <= 0

    def minutes_until_start(self) -> int:
        now = datetime.datetime.now().astimezone(None)
        return (self.start_datetime() - now).total_seconds()

    def is_over(self) -> bool:
        return self.end_time is not None

    def minutes_since_end(self) -> int:
        if self.end_time is None:
            return -1
        now = datetime.datetime.now().astimezone(None)
        return int((self.end_time - now).total_seconds() / 60)

    def last_few_events(self) -> str:
        if self.play_by_play is None or len(self.play_by_play) <= 0:
            print('game has no play_by_play events')
            return ''
        return '\n'.join([p.desc for p in self.play_by_play[-3:]])

    def next_box(self) -> (str, str, BoxScoreEntry):
        team = self.home
        abv = self.home_abv()
        if not self._bs_home:
            team = self.away
            abv = self.away_abv()
        self._bs_home = not self._bs_home
        if team is None or team.box_score is None:
            return ('', '', None)
        (ty, bs) = team.box_score.next()
        return (abv, ty, bs)

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
        else:
            self.current_game = None
        if next_game is not None:
            self.next_game = Game(next_game)
        else:
            self.next_game = None
        if last_game is not None:
            self.last_game = Game(last_game, box_score=box_score)
        else:
            self.last_game = None

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
