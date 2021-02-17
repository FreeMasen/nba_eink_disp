from nba_api.stats.endpoints import commonplayerinfo, teaminfocommon, commonteamroster, leaguegamefinder, boxscoresummaryv2, teamgamelog, scoreboardv2, playbyplayv2, boxscoresummaryv2
from nba_api.stats.endpoints import playbyplay, boxscoreadvancedv2, teamgamelogs
import nba_api.stats.library
import datetime
import re
import time
import json

WOLVES_ID = 1610612750

class Team:
    def __init__(self, id, lookup_info=True):
        abv_idx = 4
        w_idx = 9
        l_idx = 10
        cr_idx = 12
        dr_idx = 13
        self.team_id = id
        self.next_game = None
        if not lookup_info:
            return
        try:
            info = teaminfocommon.TeamInfoCommon(id)
            info_json = info.team_info_common.get_dict()['data'][0]
            self.abv = info_json[abv_idx]
            self.wins = info_json[w_idx]
            self.losses = info_json[l_idx]
            self.conf_rank = info_json[cr_idx]
            self.div_rank = info_json[dr_idx]
        except Exception as e:
            print(f'Error looking up team {id}: {e}')
            pass
        
    def fill_in_roster(self):
        name_idx = 3
        number_idx = 5
        pos_idx = 6
        id_idx = 13
        try:
            response = commonteamroster.CommonTeamRoster(
                self.team_id,
                '2020-21')
            data = response.get_dict()
            player_arrs = response_dict["resultSets"][0]['rowSet']
            self.roster = [Player(arr[name_idx], arr[number_idx], arr[pos_idx], arr[id_idx]) for arr in player_arrs]
        except:
            pass
    def find_next_game(self):
        if self.next_game is None:
            self.next_game = Game.find_next_game(self.team_id)
        elif self.next_game.status == 'Final':
            self.last_game = self.next_game
            self.next_game = Game.find_next_game(self.team_id) 
        return self.next_game
    def find_last_game(self):
        return Game.find_last_game(self.team_id)
    def current_game(self):
        self.find_next_game()
        if self.next_game is None:
            return self.last_game
        else:
            return self.next_game

class Player:
    def __init__(self, name, number, position, id):
        self.name = name
        self.number = number
        self.position = position
        self.id = id     

class Game:
    class Score:
        def __init__(self, home=0, away=0):
            self.home = home
            self.away = away
    class Event():
        period_map = ['Pre', 'Q1', 'Q2', 'Q3', 'Q4'] + (['OT'] * 10)
        def __init__(self, id, period, time, desc):
            self.id = id
            self.period_n = period
            self.period = self.period_map[period]
            self.time = time
            self.desc = desc
        def __repr__(self):
            base = f'{self.period} {self.time} {self.desc}'
            return base
    def __init__(self, date, id, home_id, away_id, status, home_score=None, away_score=None):
        self.date = date
        self.id = id
        self.home_id = home_id
        self.home_team = Team(home_id)
        self.away_id = away_id
        self.away_team = Team(away_id)
        status_re = re.compile('(\d{1,2}):(\d{2}) (am|pm) ET')
        status_list = status_re.findall(status)
        if status_list is not None and len(status_list) > 0:
            hour = int(status_list[0][0]) - 1
            minute = int(status_list[0][1])
            if status_list[0][2] == 'pm':
                hour += 12
            self.date = self.date.replace(hour=hour, minute=minute)
        self.status = status
        self.total_score = Game.Score(home_score, away_score)
        self.events = []
        self.old_events = []
        self.score = Game.Score()
        self.fetch_details()

    def is_home(self):
        return self.home_id == WOLVES_ID
    def start_time_string(self):
        time_str = ''
        if self.date.hour > 0:
            p = 'AM'
            hour = self.date.hour
            if self.date.hour > 12:
                hour -= 12
                p = 'PM'
            if self.date.minute > 0:
                time_str = f' {hour}:{self.date.minute} {p}'
            else:
                time_str = f' {hour} {p}'
        return f'{self.date.month}/{self.date.day}/{self.date.year}{time_str}'

    def find_next_game(team_id):
        dt_idx = 0
        id_idx = 2
        status_idx = 4
        home_idx = 6
        away_idx = 7
        today = datetime.date.today()
        dt_str = f"{today.year}-{today.month:02}-{today.day:02}"
        for i in range(5):
            try:
                games = scoreboardv2.ScoreboardV2(
                    i,
                    dt_str)
                for game_arr in games.game_header.get_dict()['data']:
                    if game_arr[home_idx] == team_id or game_arr[away_idx] == team_id:
                        game_dt = datetime.datetime.strptime(game_arr[dt_idx], "%Y-%m-%dT%H:%M:%S")
                        return Game(
                            game_dt,
                            game_arr[id_idx],
                            game_arr[home_idx],
                            game_arr[away_idx],
                            game_arr[status_idx]
                        )
            except Exception as e:
                print(f'Error looking up last game: {e}')
                return
    def find_last_game(team_id):
        dt_idx = 0
        id_idx = 2
        status_idx = 4
        home_idx = 6
        away_idx = 7
        today = datetime.date.today()
        dt_str = f"{today.year}-{today.month:02}-{today.day:02}"
        for i in range(-1, -5, -1):
            print('trying game', i)
            try:
                games = scoreboardv2.ScoreboardV2(
                    i,
                    dt_str)
                for game_arr in games.game_header.get_dict()['data']:
                    if game_arr[home_idx] == team_id or game_arr[away_idx] == team_id:
                        game_dt = datetime.datetime.strptime(game_arr[dt_idx], "%Y-%m-%dT%H:%M:%S")
                        ret = Game(
                            game_dt,
                            game_arr[id_idx],
                            game_arr[home_idx],
                            game_arr[away_idx],
                            game_arr[status_idx]
                        )
                        if ret.status != 'Final':
                            break
                        return ret
            except Exception as e:
                print(f'Error looking up last game: {e}')
                return
            
    def fetch_details(self):
        num_idx = 1
        period_idx = 4
        time_idx = 6
        desc_idx = 7
        desc2_idx = 8
        desc3_idx = 9
        score_idx = 10
        ty1 = 2
        ty2 = 3
        game_dets = playbyplayv2.PlayByPlayV2(self.id)
        details = list()
        gd = game_dets.play_by_play.get_dict()
        desc_idxs = [8, 7, 9]
        home = self.is_home()
        for event in gd['data']:
            ev = Game.Event(
                event[num_idx],
                event[period_idx],
                event[time_idx],
                Game.event_desc(event, home),
            )
            # print(ev)
            details.append(ev)
        self.events = details
        self.fetch_score()
    def fetch_old_details(self):
        num_idx = 1
        period_idx = 4
        time_idx = 6
        desc_idx = 7
        desc2_idx = 8
        desc3_idx = 9
        score_idx = 10
        ty1 = 2
        ty2 = 3
        game_dets = playbyplay.PlayByPlay(self.id)
        
        details = list()
        gd = game_dets.play_by_play.get_dict()
        desc_idxs = [8, 7, 9]
        home = self.is_home()
        for event in gd['data']:
            ev = Game.Event(
                event[num_idx],
                event[period_idx],
                event[time_idx],
                Game.event_desc(event, home),
            )
            print(ev)
            details.append(ev)
        self.old_events = details
    def fetch_score(self):
        game_idx = 2
        team_idx = 3
        pts_idx = 22
        dt_str = f"{self.date.year}-{self.date.month:02}-{self.date.day:02}"
        try:
            games = scoreboardv2.ScoreboardV2(0, dt_str)
            line_score = games.line_score.get_dict()
            for score in line_score['data']:
                if score[game_idx] == self.id:
                    if score[team_idx] == self.home_id:
                        print('home', score)
                        self.score.home = score[pts_idx]
                    elif score[team_idx] == self.away_id:
                        print('away', score)
                        self.score.away = score[pts_idx]
        except Exception as e:
            print(f'error looking up score: {e}')
            return
        
    def event_desc(arr, home):
        desc_idxs = [8, 7, 9]
        if not home:
            desc_idxs = [8, 9, 7]
        for idx in desc_idxs:
            if arr[idx] is not None:
                return arr[idx]
        if arr[2] == 13 and arr[3] == 0:
            return 'Quarter End'
        if arr[2] == 12 and arr[3] == 0:
            return 'Quarter Start'
    def last_event(self):
        if len(self.events) > 0:
            return self.events[-1]

print('Looking up team')
team = Team(WOLVES_ID, False)

next_game = None
# print('looking up next game')
game = team.find_next_game()
# print('looking up last game')
last_game = team.find_last_game()
while True:
    print('main loop')
    if game is not None:
        if ((game.date - datetime.datetime.now()).total_seconds() > 60 * 60):
            next_game = game
            game = None
        elif game.status == 'Final':
            last_game = game
            game = None
        if game is None:
            continue
        game.fetch_score()
        last_ev = game.last_event()
        if last_ev is not None:
            print(last_ev)
        # bs = boxscoreadvancedv2.BoxScoreAdvancedV2(game.id)
        # print(bs.team_stats.get_json())
        s = teamgamelogs.TeamGameLogs(season_nullable="2020-21",team_id_nullable=team.team_id, last_n_games_nullable=1)
        print(s.team_game_logs.get_json())
        # print(f'{game.home_team.abv} {game.away_team.abv}')
        # print(f'{game.score.home} {game.score.away}')
        time.sleep(5)
    else:
        print('no current game')
        next_game = team.find_next_game()
        sleep_s = 60
        if next_game is not None:
            time_until = (next_game.date - datetime.datetime.now()).total_seconds()
            if (time_until <= 60):
                game = next_game
                next_game = None
                continue
            print(f'{next_game.home_team.abv} v {next_game.away_team.abv} {next_game.start_time_string()}')
            sleep_s = (next_game.date - datetime.datetime.now()).total_seconds()
        if last_game is not None:
            print(f'{last_game.home_team.abv} {last_game.away_team.abv}')
            print(f'{last_game.score.home} {last_game.score.away}')
        print(f'sleeping for {sleep_s}s')
        time.sleep(sleep_s)
        