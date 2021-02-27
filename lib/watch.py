import datetime
import time
import json
import os
import typing

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from . import models

Callback = typing.Callable[[models.State], None]

def load_last_game(data_dir: str):
    return load_json(data_dir, 'last_game.json', 'last game')

def load_next_game(data_dir: str):
    return load_json(data_dir, 'next_game.json', 'next game')

def load_todays_game(data_dir: str):
    today = load_json(data_dir, 'today.json', 'today')
    if len(today) == 0:
        return None
    return today

def load_box_score(data_dir: str):
    return load_json(data_dir, 'box_score.json', 'box_score')

def load_play_by_play(data_dir: str):
    return load_json(data_dir, 'play_by_play.json', 'play by play')

def load_json(data_dir: str, file: str, name: str):
    try:
        with open(os.path.join(data_dir, file)) as file:
            return json.load(file)
    except Exception as e:
        # print(f'failed to update {name}: {e}')
        pass

def watch_data_file(data_dir: str, cb: Callback):
    global state
    state = models.State(
        load_todays_game(data_dir),
        load_play_by_play(data_dir),
        load_next_game(data_dir),
        load_last_game(data_dir),
        load_box_score(data_dir)
    )
    obs = Observer()
    handler = PatternMatchingEventHandler(['*.json'], None, False, True)

    def updated(event):
        if event.event_type not in ['created', 'modified']:
            return
        if 'today.json' in event.src_path:
            game = load_todays_game(data_dir)
            state.update_current(game, None)
        if 'next_game.json' in event.src_path:
            game = load_next_game(data_dir)
            state.update_next(game)
        elif 'box_score.json' in event.src_path:
            box_score = load_box_score(data_dir)
            state.update_last(None, box_score)
        elif 'play_by_play.json' in event.src_path:
            play_by_play = load_play_by_play(data_dir)
            state.update_current(None, play_by_play)
        elif 'last_game.json' in event.src_path:
            game = load_last_game(data_dir)
            state.update_last(game, None)

        cb(state)

    handler.on_any_event = updated
    obs.schedule(handler, data_dir)
    obs.start()
    try:
        while True:
            cb(state)
            time.sleep(60)
    finally:
        obs.stop()
        obs.join()


def start(data_dir: str, cb: Callback):
    watch_data_file(data_dir, cb)
