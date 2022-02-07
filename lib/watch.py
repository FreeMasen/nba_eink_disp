import time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import typing


class Watcher:
    # Set the directory on watch
    datafile = ""

    def __init__(self, datafile: str, render: typing.Callable[[typing.List[str]], None]):
        self.datafile = datafile
        self.render = render
        self.observer = Observer()

    def run(self):
        event_handler = Handler(self.render)
        if os.path.exists(self.datafile):
            event_handler.update(self.datafile)
        self.observer.schedule(event_handler, self.datafile, recursive = False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):

    def __init__(self, render: typing.Callable[[typing.List[str]], None]):
        self.render = render

    def on_created(self, event):
        if event.is_directory:
            return
        self.update(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.update(event.src_path)

    def update(self, path: str):
        try:
            with open(path) as f:
                contents = f.read()
        except Exception as ex:
            print(f"failed to update {ex}")
            return
        self.render(contents.splitlines())

def start(datafile: str, render: typing.Callable[[typing.List[str]], None]):
    print('start')
    watch = Watcher(datafile, render)
    watch.run()
