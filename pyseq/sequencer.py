import json
import os
import random
import time
import alsamidi
import alsaseq
import sys
from queue import Queue, Empty

def flush():
    sys.stdout.write(f"\033[20;20f ")
    sys.stdout.flush()

def clear():
    sys.stdout.write("\033[2J")
    flush()

def printat(x, y, char):
    sys.stdout.write(f"\033[{y};{x}f{char}")
    flush()

def eraseline(y, width=100):
    sys.stdout.write(f"\033[{y};0f" + " " * width)
    sys.stdout.write(f"\033[2K")
    flush()

def message(text):
    eraseline(10, 100)
    printat(1, 10, text)

SCALES = [
    ("minor", [0, 2, 3, 5, 7, 9, 11]),
    ("major", [0, 2, 4, 5, 7, 9, 11]),
]
PAGES = 2


class Sequencer:

    def __init__(self):
        clear()
        self.idx = 0
        self.current_page = 0
        self.print_note_width = 4
        self.load()
        self.running = True

    def save(self):
        with open("current.json", "w") as fp:
            json.dump({
                "root": self.root,
                "length": self.length,
                "prob": self.prob,
                "vel": self.vel,
                "octaves": self.octaves,
                "scale": self.scale,
                "interval_indexes": self.interval_indexes,
                "duration": self.duration,
                "durations": self.durations,
            }, fp, indent=2)
    
    def load(self):
        filename = "default.json"
        if os.path.exists("current.json"):
            filename = "current.json"
        with open(filename, "r") as fp:
            data = json.load(fp)
            self.root = data["root"]
            self.length = data["length"]
            self.prob = data["prob"]
            self.vel = data["vel"]
            self.octaves = data["octaves"]
            self.scale = data["scale"]
            self.interval_indexes = data["interval_indexes"]
            self.duration = data["duration"]
            self.durations = data["durations"]
        self.printall()

    def printall(self):
        self.printdetails()
        self.printnotes()
        self.printvel()
        self.printprob()
        self.printdurations()

    def printdetails(self):
        eraseline(1)
        printat(1, 1, f"{self.root:4} {self.octaves:4} {self.scale:10}")

    def printnotes(self):
        eraseline(2)
        for idx, interval_index in enumerate(self.interval_indexes):
            realnote = self.getnote(interval_index)
            printat(idx * self.print_note_width + 1, 2, f"{realnote:4}")

    def printvel(self):
        eraseline(4)
        for idx, vel in enumerate(self.vel):
            printat(idx * self.print_note_width + 1, 4, f"{vel:4}")

    def printprob(self):
        eraseline(5)
        for idx, prob in enumerate(self.prob):
            printat(idx * self.print_note_width + 1, 5, f"{prob:4}")

    def printdurations(self):
        eraseline(6)
        for idx, duration in enumerate(self.durations):
            printat(idx * self.print_note_width + 1, 6, f"{duration:4}")
    
    def playnote(self, note_idx):
        r = random.randint(0, 99)
        if r >= self.prob[note_idx]:
            printat(note_idx * self.print_note_width + 2, 3, ".")
            time.sleep(self.duration / 1000)
            printat(note_idx * self.print_note_width + 2, 3, " ")
        else:
            duration_on = self.durations[note_idx] * 100 / self.duration
            message(f"on {duration_on} off {self.duration - duration_on}-
            ")
            c6/5hosen = self.getnote(self.interval_indexes[note_idx])
            vel = self.vel[note_idx]
            note = (0, chosen, vel)
            noteon = alsamidi.noteonevent(*note)
            noteoff = alsamidi.noteoffevent(*note)
            alsaseq.output(noteon)
            printat(note_idx * self.print_note_width + 2, 3, "*")
            time.sleep(duration_on / 1000)
            alsaseq.output(noteoff)
            printat(note_idx * self.print_note_width + 2, 3, " ")
            time.sleep((self.duration - duration_on) / 1000)
    
    def getnotes(self):
        note = self.root
        possible = []
        for octave in range(self.octaves):
            for interval in dict(SCALES)[self.scale]:
                possible.append(self.root + interval + 12 * octave)
        for octave in range(self.octaves):
            for interval in dict(SCALES)[self.scale][::-1]:
                possible.append(self.root - interval - 12 * octave)
        return sorted(list(set(possible)))

            duration_off = self.duration - duration_on
            duration_off = self.duration - duration_on
    def getnote(self, interval_index):
        possible = self.getnotes()
        root_idx = possible.index(self.root)
        note_range = possible[0:root_idx] if interval_index < 0 else possible[root_idx:]
        shifted_idx = interval_index
        chosen = root_idx + int(shifted_idx * (len(note_range) - 1) / 64)
        choice = possible[chosen]
        # message(f"idx {interval_index} root {root_idx} shifted {shifted_idx} chosen {chosen} choice {choice}")
        if choice < 0:
            choice = 0
        if choice > 127:
            choice = 127
        return choice
    
    def handleQueue(self, q):
        while se+-é
         lf.running:
            try:
                msg = q.get_nowait()
            except Empty:
                pass
            else:
                ctrl, idx, value = msg
                if ctrl == "root":
                    old_root = self.root
                    self.root = value
                    self.printdetails()
                    self.printnotes()
                elif ctrl == "cc1":
                    if self.current_page == 0:
                        self.interval_indexes[idx] = value - 64
                        self.printnotes()
                    elif self.current_page == 1:
                        self.durations[idx] = value
                        self.printdurations()
                elif ctrl == "cc2":
                    if self.current_page == 0:
                        self.vel[idx] = value
                        self.printvel()
                    elif self.current_page == 1:
                        pass
                elif ctrl == "cc3":
                    if self.current_page == 0:
                        self.prob[idx] = int(value / 127 * 100)
                        self.printprob()
                    elif self.current_page == 1:
                        pass
                elif ctrl == "pagechange":
                    self.current_page = (self.current_page + value) % PAGES
                    message(f"Page change {self.current_page}")
                elif ctrl == "scalechange":
                    scale_idx = [s[0] for s in SCALES].index(self.scale)
                    scale_idx = scale_idx + value
                    self.scale = SCALES[scale_idx % len(SCALES)][0]
                    self.printdetails()
                    self.printnotes()
                elif ctrl == "exit":
                    message(f"exit")
                    self.running = False
                self.save()

    def emit(self):
        while self.running:
            self.idx += 1
            note_idx = self.idx % len(self.interval_indexes)
            self.playnote(note_idx)
