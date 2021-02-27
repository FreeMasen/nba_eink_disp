import typing
import time
import datetime

from . import util, models
state = None
last_update = datetime.datetime(1970, 1, 1)

def render(st: models.State):
    global state
    global last_update
    state = st
    if (datetime.datetime.now() - last_update).total_seconds() > 60:
        tick()
        last_update = datetime.datetime.now()

def tick():
    global state
    if state is not None:
        if state.current_game is not None:
            if not state.current_game.dirty():
                return
            print(f'{state.current_game.home_abv()} {state.current_game.away_abv()}')
            if state.current_game.has_started():
                print(f'{state.current_game.home_score()} {state.current_game.away_score()}')
                print(state.current_game.last_few_events())
            else:
                dur = util.format_duration(state.current_game.start_datetime())
                if dur is None:
                    print('Game started')
                else:
                    print(dur)
        elif state.last_game is not None and state.last_game.minutes_since_end() <= 16 * 60:
            print(f'{state.last_game.home_abv()} {state.last_game.away_abv()}')
            print(f'{state.last_game.home_score()} {state.last_game.away_score()}')
            for _ in range(12):
                (l_team, l_ty, l_bs) = state.last_game.next_box()
                (r_team, _, r_bs) = state.last_game.next_box()
                print(l_ty)
                print(f'{l_team}: {l_bs.value} {l_bs.name}')
                print(f'{r_team}: {r_bs.value} {r_bs.name}')
        elif state.next_game is not None:
            dur = util.format_duration(state.next_game.start_datetime())
            if dur is None:
                print('Game started')
            else:
                print(dur)


