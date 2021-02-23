import typing

from . import util, models


def render(state: models.State):
    if state.current_game is not None:
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
    elif state.next_game is not None:
        dur = util.format_duration(state.next_game.start_datetime())
        if dur is None:
            print('Game started')
        else:
            print(dur)
    elif state.last_game is not None:
        pass
