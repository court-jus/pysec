import curses
import logging
from functools import wraps
import time

from queue import Queue, Empty


logger = logging.getLogger()

class Exit(Exception):
    pass


def need_screen(fn):
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        if not self.screen:
            return
        fn(self, *args, **kwargs)
    return wrapped


class SequencerView:
    def __init__(self):
        self.in_q = Queue()
        self.queues = []
        self.running = True
        self.dirty = None
        self.cursor = [0, 0]
        self.cursor_max = [8, 4]

    def subscribe(self, q):
        self.queues.append(q)
    
    def publish(self, message):
        for q in self.queues:
            q.put(message)

    @need_screen
    def eraseline(self, y):
        self.screen.move(y, 1)
        self.screen.clrtoeol()
        self.dirty = time.time()

    @need_screen
    def message(self, text):
        self.eraseline(10)
        self.screen.addstr(10, 1, text, curses.color_pair(1))
        self.dirty = time.time()

    @need_screen
    def printat(self, args):
        x, y, char = args
        self.screen.addstr(y, x, char)
        self.dirty = time.time()

    def get_virtual_cursor(self):
        x, y = self.cursor
        y = y + 3 if y > 0 else 2
        x = (x + 1) * 4
        return y, x

    def change_at_cursor(self, incr=1):
        ctrl = "cc" + str(self.cursor[1] + 1)
        idx = self.cursor[0]
        val = ("relative", incr)
        self.publish((ctrl, idx, val))

    def _run(self, stdscr):
        self.screen = curses.initscr()
        # Clear screen
        self.screen.clear()
        # Initialize colors
        curses.start_color()
        # Red text on white background
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
        # Non blocking keyboard input
        self.screen.nodelay(True)
        while self.running:
            # Read the queue
            try:
                msg = self.in_q.get_nowait()
            except Empty:
                pass
            else:
                ctrl, idx, value = msg
                if ctrl in ("eraseline", "message", "printlist", "printat"):
                    getattr(self, ctrl)(value)
                if ctrl == "exit":
                    self.running = False

            # Read the keyboard
            try:
                key = self.screen.getkey(*self.get_virtual_cursor())
            except curses.error:
                pass
            else:
                if key == "q":
                    self.publish(("exit", None, None))
                    self.running = False
                elif key == "KEY_LEFT":
                    self.cursor[0] = (self.cursor[0] - 1) % self.cursor_max[0]
                elif key == "KEY_RIGHT":
                    self.cursor[0] = (self.cursor[0] + 1) % self.cursor_max[0]
                elif key == "KEY_UP":
                    self.cursor[1] = (self.cursor[1] - 1) % self.cursor_max[1]
                elif key == "KEY_DOWN":
                    self.cursor[1] = (self.cursor[1] + 1) % self.cursor_max[1]
                elif key == "+":
                    self.change_at_cursor(1)
                elif key == "-":
                    self.change_at_cursor(-1)
                elif key == "KEY_PPAGE":
                    self.change_at_cursor(10)
                elif key == "KEY_NPAGE":
                    self.change_at_cursor(-10)
                elif key == "z":
                    self.publish(("scalechange", None, 1))
                elif key == "s":
                    self.publish(("scalechange", None, -1))
                elif key == "e":
                    self.publish(("orderchange", None, 1))
                elif key == "d":
                    self.publish(("orderchange", None, -1))
                elif key == "r":
                    self.publish(("speedchange", None, 1))
                elif key == "f":
                    self.publish(("speedchange", None, -1))
                else:
                    self.message(key)
            
            # Refresh the screen
            if self.dirty is not None and time.time() - self.dirty > 5:
                self.screen.refresh()
        logger.info("Exit view")
    
    def run(self):
        curses.wrapper(self._run)