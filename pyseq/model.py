import json
import os
import random
import time
import alsamidi
import alsaseq
import logging
import sys
from queue import Queue, Empty

from pyseq.events import STOP

SCALES = [
    ("acoustic", [0, 2, 4, 6, 7, 9, 10]),
    ("blues phrygian", [0, 1, 3, 5, 6, 7, 10]),
    ("blues", [0, 3, 5, 6, 7, 10]),
    ("dorian", [0, 2, 3, 5, 7, 9, 10]),
    ("enigmatic", [0, 1, 4, 6, 8, 10, 11]),
    ("flamenco", [0, 1, 4, 5, 7, 8, 11]),
    ("hirajoshi", [0, 4, 6, 7, 11]),
    ("major", [0, 2, 4, 5, 7, 9, 11]),
    ("major locrian", [0, 2, 4, 5, 6, 8, 10]),
    ("major pentatonic", [0, 2, 4, 7, 9]),
    ("minor pentatonic", [0, 3, 5, 7, 10]),
    ("natural minor", [0, 2, 3, 5, 7, 8, 10]),
    ("octatonic1", [0, 2, 3, 5, 6, 8, 9, 11]),
    ("octatonic2", [0, 1, 3, 4, 6, 7, 9, 10]),
    ("persian", [0, 1, 4, 5, 6, 8, 11]),
    ("raga gandharavam", [0, 1, 3, 5, 7, 10]),
    ("ukrainian", [0, 2, 3, 6, 7, 9, 10]),
    ("tritone", [0, 1, 4, 6, 7, 10]),
]
PAGES = 2

logger = logging.getLogger()


class SequencerModel:

    def __init__(self):
        self.in_q = Queue()
        self.idx = 0
        self.current_page = 0
        self.print_note_width = 4
        self.queues = []
        self.load()
        self.running = True

    def subscribe(self, q):
        self.queues.append(q)
    
    def publish(self, message):
        for q in self.queues:
            q.put(message)

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

    def playnote(self, note_idx):
        r = random.randint(0, 99)
        if r >= self.prob[note_idx]:
            self.publish(("printat", None, (note_idx * self.print_note_width + 2, 3, ".")))
            time.sleep(self.duration / 1000)
            self.publish(("printat", None, (note_idx * self.print_note_width + 2, 3, " ")))
        else:
            duration_on = self.durations[note_idx] * self.duration / 127
            chosen = self.getnote(self.interval_indexes[note_idx])
            vel = self.vel[note_idx]
            note = (0, chosen, vel)
            noteon = alsamidi.noteonevent(*note)
            noteoff = alsamidi.noteoffevent(*note)
            alsaseq.output(noteon)
            self.publish(("printat", None, (note_idx * self.print_note_width + 2, 3, "*")))
            time.sleep(duration_on / 1000)
            alsaseq.output(noteoff)
            self.publish(("printat", None, (note_idx * self.print_note_width + 2, 3, " ")))
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

    def getnote(self, interval_index):
        possible = self.getnotes()
        root_idx = possible.index(self.root)
        note_range = possible[0:root_idx] if interval_index < 0 else possible[root_idx:]
        shifted_idx = interval_index
        chosen = root_idx + int(shifted_idx * (len(note_range) - 1) / 64)
        choice = possible[chosen]
        if choice < 0:
            choice = 0
        if choice > 127:
            choice = 127
        return choice
    
    def message(self, value):
        self.publish(("message", None, value))
    
    def printall(self):
        self.printdetails()
        self.printnotes()
        self.printvel()
        self.printprob()
        self.printdurations()

    def printdetails(self):
        self.publish(("eraseline", None, 1))
        self.publish(("printat", None, (1, 1, f"{self.root:4} {self.octaves:4} {self.scale:10} {self.duration:4}")))

    def printnotes(self):
        message = ""
        for idx, interval_index in enumerate(self.interval_indexes):
            realnote = self.getnote(interval_index)
            message += f"{realnote:4}"
        self.publish(("printat", None, (1, 2, message)))

    def printlist(self, y, values):
        self.publish(("printat", None, (1, y, "".join(f"{value:4}" for value in values))))

    def printvel(self):
        self.printlist(4, self.vel)

    def printprob(self):
        self.printlist(5, self.prob)

    def printdurations(self):
        self.printlist(6, self.durations)
    
    def handleQueue(self):
        self.printall()
        while self.running:
            try:
                msg = self.in_q.get_nowait()
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
                        pass
                elif ctrl == "cc2":
                    if self.current_page == 0:
                        self.vel[idx] = value
                        self.printvel()
                    elif self.current_page == 1:
                        pass
                elif ctrl == "cc3":
                    if self.current_page == 0:
                        self.durations[idx] = value
                        self.printdurations()
                    elif self.current_page == 1:
                        pass
                elif ctrl == "cc4":
                    if self.current_page == 0:
                        self.prob[idx] = int(value / 127 * 100)
                        self.printprob()
                    elif self.current_page == 1:
                        pass
                elif ctrl == "pagechange":
                    self.current_page = (self.current_page + value) % PAGES
                    self.message(f"Page change {self.current_page}")
                elif ctrl == "scalechange":
                    scale_idx = [s[0] for s in SCALES].index(self.scale)
                    scale_idx = scale_idx + value
                    self.scale = SCALES[scale_idx % len(SCALES)][0]
                    self.printdetails()
                    self.printnotes()
                elif ctrl == "speedchange":
                    self.duration += value
                    self.printdetails()
                elif ctrl == "exit":
                    self.message(f"exit")
                    alsaseq.output((STOP,0,0,0,(0,0),(0,0),(0,0),0))
                    self.running = False
                self.save()
        logger.info("Exit handle queue in model")

    def emit(self):
        running = True
        while self.running:
            self.idx += 1
            note_idx = self.idx % len(self.interval_indexes)
            self.playnote(note_idx)
        logger.info("Exit emit")
