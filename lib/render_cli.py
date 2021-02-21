from . import util


def render(game, box_score, play_by_play):
    print('cli.render')
    if game is not None:
        print(f'{game.home.abv} {game.away.abv}')
    else:
        print('HOM VIS')
    if play_by_play is not None:
        last = play_by_play[-1]
        print(f'{last["home_score"]: >3} {last["away_score"]: >3}')
        print(last["clock"])
        print(last['desc'])
    elif game is not None:
        dur = util.format_duration(game.start_datetime())
        if dur is None:
            print('Game started')
        else:
            print(dur)
