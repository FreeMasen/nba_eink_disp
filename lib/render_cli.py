

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
