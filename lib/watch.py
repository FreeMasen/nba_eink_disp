import time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import typing

logfile = open("events.log", "w+")
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
                time.sleep(0.5)
        except:
            self.observer.stop()
            print("Observer Stopped")
        logfile.close()
        self.observer.join()


class Handler(FileSystemEventHandler):

    def __init__(self, render: typing.Callable[[typing.List[str]], None]):
        self.render = render
        self.last_update = time.time() - 300

    def on_created(self, event):
        print("Created event", file=logfile, flush=True)
        if event.is_directory:
            return
        self.update(event.src_path)

    def on_modified(self, event):
        print("Modified event", file=logfile, flush=True)
        if event.is_directory:
            return
        self.update(event.src_path)

    def update(self, path: str):
        print("update", file=logfile, flush=True)
        if time.time() - self.last_update < 300 :
            return
        self.last_update = time.time()
        try:
            with open(path) as f:
                contents = f.read()
        except Exception as ex:
            print(f"failed to update {ex}", file=logfile, flush=True)
            return
        self.render(contents.splitlines())

def start(datafile: str, render: typing.Callable[[typing.List[str]], None]):
    print('start')
    watch = Watcher(datafile, render)
    watch.run()
