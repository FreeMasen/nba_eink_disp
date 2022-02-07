from sys import stderr
import curses
import typing

stdscr = curses.initscr()

def render(lines: typing.List[str]):
    global stdscr
    stdscr.clear()
    (_, width) = stdscr.getmaxyx()
    if width % 2 != 0:
        width = width - 1
    for (i, line) in enumerate(lines):
        line = line[1:].strip().center(width)
        
        stdscr.addstr(i, 0, line)
    stdscr.refresh()